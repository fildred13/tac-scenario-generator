import csv
import json
import logging
import random
from collections import defaultdict
from pathlib import Path

from tac_scenario_generator.adapters.combat_mission.driver import \
    CombatMissionDriver
from tac_scenario_generator.settings import DEBUG_DIR

logger = logging.getLogger(__name__)


# This special value is stored as the rarity value in force_data files to
# represent "infinite rarity". i.e., that the unit is not available.
INFINITE_RARITY_VALUE = 999

infinite_defaultdict = lambda: defaultdict(infinite_defaultdict)


class CombatMissionAdapter:
    """This abstract base class ensures a common interface across all the
    combat mission adapters, and provides funcitonality common across all first
    generation Combat Mission games.
    """

    def __init__(self, game_id):
        self._game_id = game_id
        self._driver = CombatMissionDriver(game_id)
        self._force_data = infinite_defaultdict()

    def generate_and_populate(self, scenario_config):
        """This method will parse the scenario config, generate a configuration
        manifest, and implement that manifest into the scenario editor.
        Presumes that the user has already navigated to the scenario editor.
        """
        # TODO: add region
        self.year = scenario_config['year']
        self.month = scenario_config['month']
        army_configs = scenario_config.get('armies')

        allied_oob, axis_oob = self.generate_oobs(army_configs)

        if allied_oob:
            self._driver.populate_oob(allied_oob)
        if axis_oob:
            self._driver.populate_oob(axis_oob)

        logger.info('Generation and population complete.')

    def generate_oob(self, army, config):
        """Returns a ready-to-populate order of battle. Presumse the adapter
        has been initialized with a year, month, and region.

        An example output oob:
        {
            'army': 'Allied',
            'nations': {
                'Canadian': {
                    'On Map': {
                        'Support': [
                            {name: 'Mortar 81mm'}
                        ]
                    }
                }
            }
        }
        """
        logger.info(f'Generating {army} OOB from this config: {config}')

        oob = {
            'army': army,
            'nations': {}
        }
        for nation, waves in config.items():
            oob['nations'][nation] = {}
            for wave, wave_unit_types in waves.items():
                oob['nations'][nation][wave] = {}
                for unit_type, unit_configs in wave_unit_types.items():
                    oob['nations'][nation][wave][unit_type] = []
                    for unit_config in unit_configs:
                        units = self._generate_units(
                            army=army, nation=nation, unit_type=unit_type, **unit_config
                        )
                        oob['nations'][nation][wave][unit_type].extend(units)
                    # TODO: could sort the units within each unit type to
                    # minimize the amount of division/fitness/etc. juggling

        # TODO: don't forget to output the oob as a debug artifact
        debug_path = DEBUG_DIR / f'{army}_oob.json'
        with open(debug_path, 'w') as f:
            json.dump(oob, f, indent=4)
        logger.debug(f'{army} oob debug artifact dumped to {debug_path}')
        logger.info(f'{army} OOB generated.')

        return oob

    def generate_oobs(self, army_configs):
        """Returns both an allied and axis oob. Returns None for any army which
        has no army configuration. Assumes the adapter has been initialized
        with a self.year, self.month, and self.region (if applicable).
        """
        allied_oob = None
        axis_oob = None
        if army_configs:
            logger.info('Generating OOBs.')
            if army_configs.get('Allied'):
                allied_oob = self.generate_oob(army='Allied', config=army_configs['Allied'])
            if army_configs.get('Axis'):
                axis_oob = self.generate_oob(army='Axis', config=army_configs['Axis'])
            logger.info('OOBs generated.')
        else:
            logger.info('No army configs provided. Skipping OOB generation.')

        return (allied_oob, axis_oob)

    def _generate_units(
            self,
            army,
            nation,
            unit_type,
            unit_name,
            division=None,
            count=1,
            count_min=None,
            count_max=None,
            chance_per_unit=100,
            chance=100,
            all_same=False
    ):
        """Generates zero or more units in oob format.

        nation (str): nation name. In CMBO, this is called the "force".
        unit_type (str): Infantry, Armor, etc. The unit types from combat
            mission. Note that Artillery and Air are considered separate unit types
            in this tool, and must be specified independently.
        unit_name (str): Name of the unit, or the special value "random" which
            will cause a random unit to be selected for each unit in the group.

        all_same (bool): If true, all units in the group will be the same unit
            type. Does not guarantee that those units will be equally
            armed/fit/etc.

        division (str): division name. in CMAK and CMBB, some units must be
            found be navigating to the correct division.

        chance (int): Percent chance out of 100 that the entire unit group is
            present. This allows you to generate a group of units of a certain
            composition, such as a platoon of the same vehicle, but then have a
            chance that the entire platoon isn't present.

        count (int): Number of units which may appear. Each potential unit has
            chance_per_unit chance to appear. if count_min and count_max are
            provided, count and chance_per_unit are ignored.
        chance_per_unit (int): integer between 0 and 100. If provided with
            count, determines the chance of each unit in the count being included.
        count_min (int): If provided with count_max, makes the number of units
            to generate a random number between these two integers. Passing
            count_min and count_max disables the count/chance_per_unit calculation.
        count_max (int): Max number of units that may appear. See count_min.
        """
        units = []

        if random.randint(1, 100) > chance:
            return units

        _count = self._get_unit_count(
            count=count, count_min=count_min, count_max=count_max, chance_per_unit=chance_per_unit
        )
        logger.debug(f'_count: {_count}')

        for i in range(0, _count):
            # If all the units are supposed to be the same and we've generated
            # one already, then keep using that same unit name.
            if i > 0 and all_same:
                _unit_name = units[0]['name']
            else:
                _unit_name = unit_name
            unit = self._generate_unit(
                army=army, nation=nation, division=division, unit_type=unit_type, unit_name=_unit_name
            )
            units.append(unit)

        return units

    def _get_force_data(self, nation, unit_type, division):
        """Retrieves force data from cache, or from disk and adds to cache."""
        # try to get force data from memory cache
        force_data = self._force_data[self._game_id][nation][unit_type][division]
        # open the appropriate force_data file based on game, army, nation, unit type and division.
        if force_data == {}:
            if division:
                file_name = f'{nation}_{unit_type}_{division}.csv'
            else:
                file_name = f'{nation}_{unit_type}.csv'
            file_name.replace(' ', '_').lower()

            force_data = []
            with open(Path(__file__).parent / self._game_id / 'force_data' / file_name, 'r') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    force_data.append(row)

            # add to the force data to the in memory cache
            self._force_data[self._game_id][nation][unit_type][division] = force_data

        return force_data

    # TODO: CMAK and CMBB have the concept of "region", which will also need to
    # be accounted for here, and in the force data files.
    def _generate_unit(self, army, nation, division, unit_type, unit_name):
        """Generates a single unit in oob format. See _generate_units for parameter descriptions."""
        if unit_name == 'random':
            force_data = self._get_force_data(nation=nation, unit_type=unit_type, division=division)
            logger.debug(f'force data: {force_data}')
            rarity_key = f'{self.month}_{self.year}_rarity'
            force_data = [i for i in force_data if i[rarity_key] != INFINITE_RARITY_VALUE]
            unit_names = [unit['unit'] for unit in force_data]
            weights = [int(100 / ((100 + int(unit[rarity_key])) / 100)) for unit in force_data]
            _unit_name = random.choices(unit_names, weights=weights)[0]
        else:
            _unit_name = unit_name

        unit = {'name': _unit_name}

        return unit

    def _get_unit_count(self, count, count_min, count_max, chance_per_unit):
        """See _generate_units() for parameter explanations."""
        if (count_min is not None and count_max is None) or (count_max is not None and count_min is None):
            raise ValueError('if count_min is provided, count_max must also be provided.')
        elif count_min is not None and count_max is not None:
            if count_min >= count_max:
                raise ValueError('count_min must be less that count_max.')
            _count = random.randint(count_min, count_max)
        else:
            _count = 0
            for _ in range(0, count):
                if random.randint(1, 100) < chance_per_unit:
                    _count += 1

        return _count
