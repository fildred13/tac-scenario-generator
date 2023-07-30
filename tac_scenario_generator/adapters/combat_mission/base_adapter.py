from abc import ABC, abstractmethod


class CombatMissionAdapterABC(ABC):
    """This abstract base class ensures a common interface across all the
    combat mission adapters, and provides funcitonality common across all first
    generation Combat Mission games.
    """

    @abstractmethod
    def method_to_implement(self):
        """Abstract method that must be implemented by subclasses."""
        pass

    def common_method(self):
        """A method that is common to all subclasses."""
        # Add your implementation here
        pass
