import os
from PIL import Image

def analyze_base_textures(output_dir):
    """分析并保存 face 和 body 的 base 贴图的 R,G,B 通道，用于诊断。"""
    base_output_dir = os.path.join(output_dir, "channel_analysis")
    os.makedirs(base_output_dir, exist_ok=True)
    
    parts_to_analyze = {
        "face": "1003_Tokai Teio/Texture2D/tex_chr1003_00_face_base.png",
        "body": "1003_Tokai Teio/Texture2D/tex_bdy1003_00_base.png"
    }

    print("开始分析贴图通道...")
    for part_name, path in parts_to_analyze.items():
        try:
            with Image.open(path) as img:
                # 统一尺寸以便对比
                if part_name == 'body':
                    img = img.resize((512, 512))

                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                r, g, b, _ = img.split()

                part_output_dir = os.path.join(base_output_dir, part_name + "_channels")
                os.makedirs(part_output_dir, exist_ok=True)

                r.save(os.path.join(part_output_dir, f"{part_name}_R_shadow_mask.png"))
                g.save(os.path.join(part_output_dir, f"{part_name}_G_specular_mask.png"))
                b.save(os.path.join(part_output_dir, f"{part_name}_B_cutoff_mask.png"))
                
                print(f"已保存 {part_name} 的 R,G,B 通道到: {part_output_dir}")

        except FileNotFoundError:
            print(f"错误: 找不到文件 {path}")
        except Exception as e:
            print(f"处理 {path} 时发生错误: {e}")

if __name__ == "__main__":
    analyze_base_textures("./processed_results") 