from PIL import Image, ImageChops, ImageEnhance
import os

# 兼容不同Pillow版本
try:
    from PIL.Image import Resampling
    RESIZE_FILTER = Resampling.LANCZOS
except ImportError:
    RESIZE_FILTER = Image.LANCZOS

def process_eye_highlights(base_path, highlight_paths, output_dir):
    """恢复用户最初的眼睛高光处理逻辑，仅输出最终结果。"""
    os.makedirs(output_dir, exist_ok=True)
    base_img = Image.open(base_path).convert('RGB')

    # 初始化处理区域 (左眼和右眼)
    # 假设眼部贴图是垂直排列的，高光贴图尺寸为单眼尺寸
    h_img_size = Image.open(highlight_paths[0]).size
    left_eye = base_img.crop((0, 0, h_img_size[0], h_img_size[1]))
    right_eye_y_offset = h_img_size[1]
    right_eye = base_img.crop((0, right_eye_y_offset, h_img_size[0], right_eye_y_offset + h_img_size[1]))

    # 遍历高光贴图并叠加
    for hl_path in highlight_paths:
        hl_img = Image.open(hl_path).convert('RGB')
        
        # 叠加高光
        left_eye = ImageChops.add(left_eye, hl_img)
        right_eye = ImageChops.add(right_eye, hl_img)

        # 数值截断
        left_eye = Image.eval(left_eye, lambda x: min(x, 255))
        right_eye = Image.eval(right_eye, lambda x: min(x, 255))

    # 生成最终合成图
    final_img = base_img.copy()
    final_img.paste(left_eye, (0, 0))
    final_img.paste(right_eye, (0, right_eye_y_offset))
    
    # 保存最终结果
    output_path = os.path.join(output_dir, "eye_final.png")
    final_img.save(output_path)
    print(f"眼睛最终贴图已恢复并保存到: {output_path}")
    return final_img


def process_part(part_name, paths, output_dir, sharpen_contrast=1.8, apply_specular=True, apply_cutoff=True):
    """
    根据Bilibili文章流程处理单个部位的贴图.
    流程: 基础色 -> 叠加阴影 -> 叠加高光(可选) -> 应用透明通道(可选).
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"正在处理部位: {part_name}...")

    # 1. 加载贴图
    try:
        diff_img = Image.open(paths['diff']).convert('RGBA')
        base_img = Image.open(paths['base']).convert('RGBA')
        shad_c_img = Image.open(paths['shad_c']).convert('RGB')
    except FileNotFoundError as e:
        print(f"错误: {part_name} 缺少贴图文件 {e.filename}, 跳过该部位。")
        return

    # 2. 统一尺寸 (以diff贴图为基准)
    if base_img.size != diff_img.size:
        base_img = base_img.resize(diff_img.size, RESIZE_FILTER)
    if shad_c_img.size != diff_img.size:
        shad_c_img = shad_c_img.resize(diff_img.size, RESIZE_FILTER)

    # 分离base贴图的通道
    r, g, b, _ = base_img.split()

    # --- 步骤1: 处理阴影 ---
    # base红色通道作为阴影蒙版, 增强对比度并反相
    shadow_mask = ImageEnhance.Contrast(r).enhance(sharpen_contrast)
    shadow_mask = ImageChops.invert(shadow_mask)
    # 使用蒙版将shad_c混合到diff上
    # lerp(diff, shad_c, mask) -> Image.composite(shad_c, diff, mask)
    result_img = Image.composite(shad_c_img, diff_img.convert('RGB'), shadow_mask)

    # --- 步骤2: 处理高光 (可选) ---
    if apply_specular:
        print(f"  - 为 {part_name} 应用高光...")
        # base绿色通道作为高光蒙版
        _, g, _, _ = base_img.split()
        specular_mask = g
        # 创建高光层 (白色, add模式)
        highlight_layer = Image.new('RGB', diff_img.size, (0, 0, 0))
        white_color = Image.new('RGB', diff_img.size, (255, 255, 255))
        highlight_layer.paste(white_color, mask=specular_mask)
        result_img = ImageChops.add(result_img, highlight_layer)
        result_img = Image.eval(result_img, lambda x: min(x, 255)) # clip

    # --- 步骤3: 处理透明通道 (可选) ---
    result_img = result_img.convert('RGBA')
    if apply_cutoff:
        print(f"  - 为 {part_name} 应用透明通道...")
        # base蓝色通道直接作为最终alpha通道
        _, _, b, _ = base_img.split()
        result_img.putalpha(b)

    # 保存最终结果
    output_path = os.path.join(output_dir, f"{part_name}_final.png")
    result_img.save(output_path)
    print(f"{part_name} 最终贴图已保存到: {output_path}")
    return result_img


# --- 路径配置 ---
texture_dir = "1003_Tokai Teio/Texture2D"
output_root_dir = "./processed_results"

# 眼睛贴图
eye_base = os.path.join(texture_dir, "tex_chr1003_00_eye0.png")
eye_highlights = [
    os.path.join(texture_dir, "tex_chr1003_00_eyehi00.png"),
    os.path.join(texture_dir, "tex_chr1003_00_eyehi01.png") # 根据用户要求, 只用前两个
]

# 其他部位贴图
parts_paths = {
    "face": {
        "diff": os.path.join(texture_dir, "tex_chr1003_00_face_diff.png"),
        "base": os.path.join(texture_dir, "tex_chr1003_00_face_base.png"),
        "shad_c": os.path.join(texture_dir, "tex_chr1003_00_face_shad_c.png"),
    },
    "hair": {
        "diff": os.path.join(texture_dir, "tex_chr1003_00_hair_diff.png"),
        "base": os.path.join(texture_dir, "tex_chr1003_00_hair_base.png"),
        "shad_c": os.path.join(texture_dir, "tex_chr1003_00_hair_shad_c.png"),
    },
    "body": {
        "diff": os.path.join(texture_dir, "tex_bdy1003_00_diff.png"),
        "base": os.path.join(texture_dir, "tex_bdy1003_00_base.png"),
        "shad_c": os.path.join(texture_dir, "tex_bdy1003_00_shad_c.png"),
    },
    "tail": {
        "diff": os.path.join(texture_dir, "tex_tail0001_00_1003_diff.png"),
        "base": os.path.join(texture_dir, "tex_tail0001_00_0000_base.png"),
        "shad_c": os.path.join(texture_dir, "tex_tail0001_00_1003_shad_c.png"),
    }
}

# --- 执行处理 ---
# 处理眼睛
eye_final_img = process_eye_highlights(
    base_path=eye_base,
    highlight_paths=eye_highlights,
    output_dir=os.path.join(output_root_dir, "eye")
)
# eye_final_img.show()

# 处理其他部位
for part_name, paths in parts_paths.items():
    # 脸部不应用高光和透明通道处理，其他部位应用
    use_specular = (part_name != 'face')
    use_cutoff = (part_name != 'face')

    part_final_img = process_part(
        part_name,
        paths,
        output_dir=os.path.join(output_root_dir, part_name),
        apply_specular=use_specular,
        apply_cutoff=use_cutoff
    )
    if part_final_img:
        # pass
        part_final_img.show()