import logging

from tac_scenario_generator.adapters.combat_mission.driver import CombatMissionDriver


logger = logging.getLogger(__name__)


class CombatMissionAdapter:
    """This abstract base class ensures a common interface across all the
    combat mission adapters, and provides funcitonality common across all first
    generation Combat Mission games.
    """

    def __init__(self, game_id):
        self._game_id = game_id
        self._driver = CombatMissionDriver(game_id)

    def generate_and_populate(self, scenario_config):
        """This method will parse the scenario config, generate a configuration
        manifest, and implement that manifest into the scenario editor.
        Presumes that the user has already navigated to the scenario editor.
        """
        year = scenario_config['year']
        month = scenario_config['month']
        army_configs = scenario_config.get('armies')

        allied_oob, axis_oob = self.generate_oobs(year, month, army_configs)

        if allied_oob:
            self._populate_oob(allied_oob)
        if axis_oob:
            self._populate_oob(axis_oob)

        logger.info('Generation and population complete.')

    def generate_oob(self, year, month, army, config):
        """Returns a ready-to-populate order of battle."""
        logger.info(f'Generating {army} OOB.')

        oob = {
            'army': army,
            'nations': {}
        }
        # TODO: finish this

        # TODO: don't forget to output the oob as a debug artifact
        logger.info(f'{army} OOB generated.')

        return oob

    def generate_oobs(self, year, month, army_configs):
        """Returns both an allied and axis oob. Returns None for any army which
        has no army configuration.
        """
        allied_oob = None
        axis_oob = None
        if army_configs:
            logger.info('Generating OOBs.')
            if army_configs.get('Allied'):
                allied_oob = self.generate_oob(year=year, month=month, army='Allied', config=army_configs['Allied'])
            if army_configs.get('Axis'):
                axis_oob = self.generate_oob(year=year, month=month, army='Axis', config=army_configs['Axis'])
            logger.info('OOBs generated.')
        else:
            logger.info('No army configs provided. Skipping OOB generation.')

        return (allied_oob, axis_oob)

    def _populate_oob(self, oob):
        """Given an OOB as prepared by generate_oob(), populate the units for
        the oob into the editor. Presumes that the screen is already navigated
        to the main scenario editor screen.
        """
        logger.info(f'Populating {oob["army"]} OOB')
        # Click 'Unit Editor'
        self._driver.go_to_unit_editor()
        # Select correct army
        # For each nation...
        #    # Select the correct Nation
        #    # Select the correct wave (on-map, reinforce 1, etc.)
        #    # For each unit type...
        #        # for each unit...
        #            # add the unit
        # TODO: I think all of this needs to go inside the driver,
        # This is the wrong level of abstraction for the adapter.
        self._driver.go_to_scenario_editor()
        logger.info(f'Finished populating {oob["army"]} OOB')
        
