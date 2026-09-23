import os
import numpy as np
import torch
from PIL import Image, ImageOps
import folder_paths

MODEL_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".pt2", ".pkl", ".sft")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")

ALL_FOLDERS = "<ALL>"

# Список источников: (ключ folder_paths, отображаемый префикс)
MODEL_SOURCES = [
    ("checkpoints", "CKPT"),
    ("diffusion_models", "DIFF"),
]


def get_model_roots():
    """Возвращает список (источник, корневая_папка) для checkpoints и diffusion_models."""
    roots = []
    for source_key, _ in MODEL_SOURCES:
        base_dir = folder_paths.get_folder_paths(source_key)
        if not base_dir:
            base_dir = [os.path.join(folder_paths.models_dir, source_key)]
        for p in base_dir:
            if os.path.isdir(p):
                roots.append((source_key, p))
    return roots


def get_model_list():
    """
    Рекурсивно собирает все модели из checkpoints и diffusion_models.
    Возвращает список словарей: {"source": ..., "rel": ..., "display": ...}
    """
    model_files = []
    for source_key, model_root in get_model_roots():
        for root, _, files in os.walk(model_root):
            for f in files:
                if f.lower().endswith(MODEL_EXTENSIONS):
                    full_path = os.path.join(root, f)
                    rel = os.path.relpath(full_path, model_root).replace("\\", "/")
                    model_files.append({
                        "source": source_key,
                        "rel": rel,
                        "display": f"{source_key}/{rel}",
                    })

    model_files.sort(key=lambda x: x["display"])
    return model_files


def get_model_folders_with_counts():
    """
    Возвращает dict: ключ_папки -> количество моделей.
    Ключ формируется как "source" или "source/подпапка".
    """
    models = get_model_list()
    counts = {}
    for m in models:
        source = m["source"]
        rel = m["rel"]
        folder = os.path.dirname(rel)

        if folder:
            top = folder.split("/")[0]
            key = f"{source}/{top}"
        else:
            key = source

        counts[key] = counts.get(key, 0) + 1
    return counts


def find_preview_image(source_key: str, model_rel_path: str) -> str:
    """Ищет изображение с тем же именем, что и модель (без расширения) в указанном источнике."""
    base_name = os.path.splitext(model_rel_path)[0]

    base_dir = folder_paths.get_folder_paths(source_key)
    if not base_dir:
        base_dir = [os.path.join(folder_paths.models_dir, source_key)]

    for model_root in base_dir:
        if not os.path.isdir(model_root):
            continue

        candidate_base = os.path.join(model_root, base_name.replace("/", os.sep))
        candidate_dir = os.path.dirname(candidate_base)
        candidate_file = os.path.basename(candidate_base)

        if not os.path.isdir(candidate_dir):
            continue

        for ext in IMAGE_EXTENSIONS:
            candidate = os.path.join(candidate_dir, candidate_file + ext)
            if os.path.isfile(candidate):
                return candidate

        # регистронезависимый поиск
        for f in os.listdir(candidate_dir):
            name, e = os.path.splitext(f)
            if name.lower() == candidate_file.lower() and e.lower() in IMAGE_EXTENSIONS:
                return os.path.join(candidate_dir, f)

    return ""


def load_image_tensor(path: str) -> torch.Tensor:
    """Загружает изображение в тензор [1, H, W, C] (0..1). Пусто -> чёрный квадрат 64x64."""
    if not path or not os.path.isfile(path):
        return torch.zeros((1, 64, 64, 3), dtype=torch.float32)

    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        arr = np.array(img).astype(np.float32) / 255.0
        tensor = torch.from_numpy(arr)[None,]  # [1, H, W, 3]
        return tensor
    except Exception:
        return torch.zeros((1, 64, 64, 3), dtype=torch.float32)


class ModelByIndexNode:
    @classmethod
    def INPUT_TYPES(cls):
        counts = get_model_folders_with_counts()
        total = sum(counts.values())

        folder_choices = [f"{ALL_FOLDERS} ({total})"]
        for name in sorted(counts.keys()):
            folder_choices.append(f"{name} ({counts[name]})")

        return {
            "required": {
                "folder": (folder_choices, {
                    "default": folder_choices[0],
                }),
                "index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "control_after_generate": True,
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "IMAGE", "STRING")
    RETURN_NAMES = (
        "model_basename",
        "model_name",
        "preview_image",
        "model_list",
    )
    FUNCTION = "get_model_name"
    CATEGORY = "model_utils"

    def get_model_name(self, folder: str, index: int):
        model_files = get_model_list()

        empty_img = torch.zeros((1, 64, 64, 3), dtype=torch.float32)

        if not model_files:
            return ("", "", empty_img, "")

        # Парсим выбранную папку: "CKPT (10)" -> "CKPT", "DIFF (5)" -> "DIFF",
        # "CKPT/sdxl (3)" -> "CKPT/sdxl"
        folder_key = folder.split(" (")[0]

        if folder_key and folder_key != ALL_FOLDERS:
            # Определяем источник и (возможно) подпапку
            if "/" in folder_key:
                source_part, sub_part = folder_key.split("/", 1)
            else:
                source_part, sub_part = folder_key, ""

            # Сопоставляем префикс (CKPT/DIFF) с реальным ключом folder_paths
            source_map = {prefix: key for key, prefix in MODEL_SOURCES}
            real_source = source_map.get(source_part, source_part)

            filtered = []
            for m in model_files:
                if m["source"] != real_source:
                    continue
                if sub_part:
                    prefix = sub_part + "/"
                    if m["rel"].startswith(prefix):
                        filtered.append(m)
                else:
                    filtered.append(m)
            model_files = filtered

        count_dir = len(model_files)

        if count_dir == 0:
            return ("", "", empty_img, "")

        model_list_text = "\n".join(
            f"{i}: [{m['source']}] {m['rel']}" for i, m in enumerate(model_files)
        )

        if index < 0 or index >= count_dir:
            return ("", "", empty_img, model_list_text)

        selected = model_files[index]
        model_name = selected["rel"]
        model_basename = os.path.splitext(os.path.basename(model_name))[0]
        preview_image_path = find_preview_image(selected["source"], model_name)
        preview_image = load_image_tensor(preview_image_path)

        return (
            model_basename,
            model_name,
            preview_image,
            model_list_text,
        )


NODE_CLASS_MAPPINGS = {
    "ModelByIndexNode": ModelByIndexNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ModelByIndexNode": "Model by Index (checkpoints + diffusion_models)"
}