import pytest
from decider import Decider

#TODO: hmmm, asi nutny refaktoring


@pytest.fixture()
def decider():
    return Decider()


if __name__ == "__main__":
    pass