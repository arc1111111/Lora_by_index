from .lora_by_index_node import LoraByIndexNode
from .model_by_index import ModelByIndexNode

NODE_CLASS_MAPPINGS = {
    "LoraByIndexNode": LoraByIndexNode,
    "ModelByIndexNode": ModelByIndexNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraByIndexNode": "LoRA By Index",
    "ModelByIndexNode": "Model by Index (diffusion_models)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]