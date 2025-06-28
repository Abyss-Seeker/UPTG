import os
import sys
import glob
import argparse
from PIL import Image, ImageChops, ImageEnhance

# 兼容不同Pillow版本
try:
    from PIL.Image import Resampling
    RESIZE_FILTER = Resampling.LANCZOS
except ImportError:
    RESIZE_FILTER = Image.LANCZOS

def safe_substitute_file(target_path):
    """如果目标文件存在，则重命名为 *_original.png，避免覆盖丢失。"""
    if os.path.exists(target_path):
        base, ext = os.path.splitext(target_path)
        backup_path = base + '_original' + ext
        # 如果已经有_original，避免覆盖
        idx = 1
        while os.path.exists(backup_path):
            backup_path = f"{base}_original{idx}{ext}"
            idx += 1
        os.rename(target_path, backup_path)
        print(f"      - 已将原文件重命名为: {os.path.basename(backup_path)}")

def process_eye_highlights(base_path, highlight_paths, output_dir, overwrite=False, substitute=False):
    """恢复用户最初的眼睛高光处理逻辑，仅输出最终结果。"""
    if not base_path or not highlight_paths:
        print("  - 警告: 缺少眼睛贴图，跳过处理。")
        return
    print("  - 正在处理眼睛...")

    base_img = Image.open(base_path).convert('RGB')
    h_img_size = Image.open(highlight_paths[0]).size
    left_eye = base_img.crop((0, 0, h_img_size[0], h_img_size[1]))
    right_eye_y_offset = h_img_size[1]
    right_eye = base_img.crop((0, right_eye_y_offset, h_img_size[0], right_eye_y_offset + h_img_size[1]))

    # 遍历高光贴图并叠加
    for hl_path in highlight_paths:
        hl_img_rgba = Image.open(hl_path).convert('RGBA')
        
        # 使用Alpha通道精确提取高光，避免背景色污染
        highlight_layer = Image.new('RGB', left_eye.size, (0, 0, 0))
        highlight_layer.paste(hl_img_rgba, mask=hl_img_rgba.getchannel('A'))

        # 叠加干净的高光层
        left_eye = ImageChops.add(left_eye, highlight_layer)
        right_eye = ImageChops.add(right_eye, highlight_layer)

        # 数值截断
        left_eye = Image.eval(left_eye, lambda x: min(x, 255))
        right_eye = Image.eval(right_eye, lambda x: min(x, 255))

    final_img = base_img.copy()
    final_img.paste(left_eye, (0, 0))
    final_img.paste(right_eye, (0, right_eye_y_offset))
    
    # 根据参数决定输出文件名
    if substitute:
        output_path = base_path
        safe_substitute_file(output_path)
    elif overwrite:
        output_path = base_path
    else:
        output_path = os.path.join(output_dir, "eye_final.png")
    
    final_img.save(output_path)
    print(f"    - 眼睛最终贴图已保存到: {output_path}")

def process_part(part_name, paths, output_dir, sharpen_contrast=1.8, apply_specular=True, apply_cutoff=True, overwrite=False, substitute=False):
    """根据Bilibili文章流程处理单个部位的贴图。"""
    diff_path = paths.get('diff')
    base_path = paths.get('base')
    shad_c_path = paths.get('shad_c')

    # 安全检查：确保所有必需的贴图都已找到
    if not all([diff_path, base_path, shad_c_path]):
        print(f"  - 警告: 部位 '{part_name}' 缺少一个或多个关键贴图，跳过处理。")
        return

    print(f"  - 正在处理部位: {part_name}...")
    diff_img = Image.open(diff_path).convert('RGBA')
    base_img = Image.open(base_path).convert('RGBA')
    shad_c_img = Image.open(shad_c_path).convert('RGB')

    if base_img.size != diff_img.size:
        base_img = base_img.resize(diff_img.size, RESIZE_FILTER)
    if shad_c_img.size != diff_img.size:
        shad_c_img = shad_c_img.resize(diff_img.size, RESIZE_FILTER)

    shadow_mask = ImageEnhance.Contrast(base_img.split()[0]).enhance(sharpen_contrast)
    shadow_mask = ImageChops.invert(shadow_mask)
    result_img = Image.composite(shad_c_img, diff_img.convert('RGB'), shadow_mask)

    if apply_specular:
        specular_mask = base_img.split()[1]
        highlight_layer = Image.new('RGB', diff_img.size, (0, 0, 0))
        white_color = Image.new('RGB', diff_img.size, (255, 255, 255))
        highlight_layer.paste(white_color, mask=specular_mask)
        result_img = ImageChops.add(result_img, highlight_layer)
        result_img = Image.eval(result_img, lambda x: min(x, 255))

    result_img = result_img.convert('RGBA')
    if apply_cutoff:
        result_img.putalpha(base_img.split()[2])

    # 根据参数决定输出文件名
    if substitute:
        output_path = diff_path
        safe_substitute_file(output_path)
    elif overwrite:
        output_path = diff_path
    else:
        output_path = os.path.join(output_dir, f"{part_name}_final.png")
    
    result_img.save(output_path)
    print(f"    - {part_name} 最终贴图已保存到: {output_path}")


def find_texture_files(texture_dir):
    """在指定目录中自动查找贴图文件。"""
    files = {}
    
    def find_file(pattern):
        results = glob.glob(os.path.join(texture_dir, pattern))
        return results[0] if results else None

    # 查找各部位贴图 (身体部位特殊处理)
    parts = ["face", "hair", "tail"]
    for part in parts:
        files[part] = {
            'diff': find_file(f"*{part}*diff*.png"),
            'base': find_file(f"*{part}*base*.png"),
            'shad_c': find_file(f"*{part}*shad_c*.png")
        }
    
    # 智能处理身体部位，兼容 "bdy" 和 "body"
    files['body'] = {
        'diff': find_file("*bdy*diff*.png") or find_file("*body*diff*.png"),
        'base': find_file("*bdy*base*.png") or find_file("*body*base*.png"),
        'shad_c': find_file("*bdy*shad_c*.png") or find_file("*body*shad_c*.png"),
    }
    
    # 查找眼睛贴图 (使用所有eyehi文件)
    files['eye'] = {
        'base': find_file("*eye0.png"),
        'highlights': sorted(glob.glob(os.path.join(texture_dir, "*eyehi*.png")))[:2]
    }
    
    return files

def main(model_root_dir, overwrite=False, substitute=False):
    """自动化处理模型贴图的主函数。"""
    texture_dir = os.path.join(model_root_dir, "Texture2D")
    if not os.path.isdir(texture_dir):
        print(f"错误: 在 '{model_root_dir}' 中找不到 'Texture2D' 文件夹。")
        return

    print(f"开始处理模型: {os.path.basename(model_root_dir)}")
    print(f"贴图文件夹: {texture_dir}")
    if substitute:
        print("模式: 替换原文件并备份(_original)")
    elif overwrite:
        print("模式: 覆盖原始文件")
    else:
        print("模式: 创建新文件")

    # 查找所有需要的贴图
    texture_paths = find_texture_files(texture_dir)
    
    # 处理眼睛
    process_eye_highlights(
        texture_paths['eye']['base'], 
        texture_paths['eye']['highlights'], 
        texture_dir,
        overwrite=overwrite,
        substitute=substitute
    )

    # 处理其他部位
    for part_name in ["face", "hair", "body", "tail"]:
        use_specular = (part_name != 'face')
        use_cutoff = (part_name != 'face')
        process_part(
            part_name,
            texture_paths[part_name],
            texture_dir,
            apply_specular=use_specular,
            apply_cutoff=use_cutoff,
            overwrite=overwrite,
            substitute=substitute
        )
    print("所有处理已完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='处理PMX模型贴图')
    parser.add_argument('model_path', help='包含Texture2D文件夹的模型路径')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--overwrite', action='store_true', help='覆盖原始文件而不是创建新文件')
    group.add_argument('--substitute', action='store_true', help='将原始文件重命名为*_original，再用新文件替换原名')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.model_path):
        print(f"错误: 提供的路径 '{args.model_path}' 不是一个有效的文件夹。")
        sys.exit(1)

    main(args.model_path, overwrite=args.overwrite, substitute=args.substitute) 