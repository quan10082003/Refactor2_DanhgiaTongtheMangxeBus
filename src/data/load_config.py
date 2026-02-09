from omegaconf import OmegaConf

def load_config(path: str):
    """
    Load yaml config bằng OmegaConf
    - Truy cập bằng config.A.B
    - Tự resolve biến ${}
    """
    cfg = OmegaConf.load(path)
    OmegaConf.resolve(cfg)
    return cfg

