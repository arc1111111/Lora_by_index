import os
import numpy as np
import torch
from PIL import Image, ImageOps
import folder_paths

LORA_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".pt2", ".pkl", ".sft")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")

ALL_FOLDERS = "<ALL>"


def get_lora_roots():
    base_dir = folder_paths.get_folder_paths("loras")
    if not base_dir:
        base_dir = [os.path.join(folder_paths.models_dir, "loras")]
    return [p for p in base_dir if os.path.isdir(p)]


def get_lora_list():
    lora_files = []
    for lora_root in get_lora_roots():
        for root, _, files in os.walk(lora_root):
            for f in files:
                if f.lower().endswith(LORA_EXTENSIONS):
                    full_path = os.path.join(root, f)
                    rel = os.path.relpath(full_path, lora_root)
                    lora_files.append(rel.replace("\\", "/"))

    lora_files.sort()
    return lora_files


def get_lora_folders_with_counts():
    """Возвращает dict: имя_папки -> количество LoRA в ней (верхний уровень)."""
    loras = get_lora_list()
    counts = {}
    for rel in loras:
        folder = os.path.dirname(rel)
        if folder:
            top = folder.split("/")[0]
            counts[top] = counts.get(top, 0) + 1
    return counts


def find_preview_image(lora_rel_path: str) -> str:
    """Ищет изображение с тем же именем, что и LoRA (без расширения)."""
    base_name = os.path.splitext(lora_rel_path)[0]

    for lora_root in get_lora_roots():
        candidate_base = os.path.join(lora_root, base_name.replace("/", os.sep))
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
    """Загружает изображение в тензор [1, H, W, C] (0..1). Пусто -> чёрный квадрат."""
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


def format_strength(value: float) -> str:
    """Форматирует силу Lora: убирает лишние нули и точку, если число целое."""
    if value == int(value):
        return str(int(value))
    # Округляем до 4 знаков и убираем хвостовые нули
    return f"{value:.4f}".rstrip("0").rstrip(".")


class LoraByIndexNode:
    @classmethod
    def INPUT_TYPES(cls):
        counts = get_lora_folders_with_counts()
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
                    # Включает меню "control_after_generate" (fixed / increment / decrement / randomize)
                    "control_after_generate": True,
                }),
                "lora_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": -10.0,
                    "max": 10.0,
                    "step": 0.05,
                }),
            }
        }

    RETURN_TYPES = ("STRING", "COMBO", "INT", "STRING", "STRING", "IMAGE", "STRING", "FLOAT")
    RETURN_NAMES = (
        "lora_basename",
        "lora_name",
        "count_dir",
        "lora_list",
        "preview_image_path",
        "preview_image",
        "lora_basename_for_stack",
        "lora_strength",
    )
    FUNCTION = "get_lora_name"
    CATEGORY = "lora"

    def get_lora_name(self, folder: str, index: int, lora_strength: float = 1.0):
        lora_files = get_lora_list()

        empty_img = torch.zeros((1, 64, 64, 3), dtype=torch.float32)

        if not lora_files:
            return ("", "", 0, "", "", empty_img, "", lora_strength)

        folder_name = folder.split(" (")[0]

        if folder_name and folder_name != ALL_FOLDERS:
            prefix = folder_name + "/"
            lora_files = [p for p in lora_files if p.startswith(prefix)]

        count_dir = len(lora_files)

        if count_dir == 0:
            return ("", "", 0, "", "", empty_img, "", lora_strength)

        lora_list_text = "\n".join(f"{i}: {name}" for i, name in enumerate(lora_files))

        if index < 0 or index >= count_dir:
            return ("", "", count_dir, lora_list_text, "", empty_img, "", lora_strength)

        lora_name = lora_files[index]
        lora_basename = os.path.splitext(os.path.basename(lora_name))[0]
        preview_image_path = find_preview_image(lora_name)
        preview_image = load_image_tensor(preview_image_path)

        # Формируем строку для стека с учётом силы: <lora:Ember_Cel_krea:0.8>
        strength_str = format_strength(lora_strength)
        lora_basename_for_stack = f"<lora:{lora_basename}:{strength_str}>"

        return (
            lora_basename,
            lora_name,
            count_dir,
            lora_list_text,
            preview_image_path,
            preview_image,
            lora_basename_for_stack,
            lora_strength,
        )