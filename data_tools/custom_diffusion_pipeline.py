from typing import Dict, List, Any

class EndpointHandler():
    def __init__(self, path=""):
        # Preload all the elements you are going to need at inference.
        # pseudo:
        # self.model= load_model(path)

    def __call__(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
       data args:
            inputs (:obj: `str` | `PIL.Image` | `np.array`)
            kwargs
      Return:
            A :obj:`list` | `dict`: will be serialized and returned
        """

        # pseudo
        # self.model(input)