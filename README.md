# UPTG - Uma PMX Texture Generator

Uma Pmx Texture Generator! 对从 Uma Viewer 中提取的 pmx 模型进行处理，合成几个还算不错的简单粗暴的材质文件~

一个用于处理 PMX 模型纹理的自动化工具，能够智能合成和处理各种贴图通道，生成高质量的最终纹理。

## 🎯 项目简介

UPTG (Uma PMX Texture Generator) 是一个专门为 PMX 模型设计的纹理处理工具。它能够：

- 自动识别和加载各种贴图文件
- 智能合成阴影、高光和透明通道
- 处理眼睛高光效果
- 生成高质量的最终纹理

## 📚 参考来源

本项目基于 [Bilibili 上的技术文章](https://www.bilibili.com/opus/671644048083124224) 提供的处理流程开发。

## 📁 项目结构

```
highlight_pmx/
├── main.py                 # 主处理脚本（针对特定模型）
├── process_model.py        # 通用模型处理脚本
├── check_textures.py       # 纹理分析和诊断工具
├── README.md              # 项目说明文档
├── [模型文件夹]/           # 各个角色的模型文件夹
│   ├── [模型名].pmx       # PMX 模型文件
│   └── Texture2D/         # 纹理文件夹
│       ├── tex_*_diff.png # 漫反射贴图
│       ├── tex_*_base.png # 基础贴图（包含通道信息）
│       ├── tex_*_shad_c.png # 阴影贴图
│       └── tex_*_eyehi*.png # 眼睛高光贴图
└── processed_results/     # 处理结果输出文件夹
```

## 🚀 快速开始

### 环境要求

- Python 3.6+
- Pillow (PIL) 库

### 安装依赖

```bash
pip install Pillow
```

### 使用方法

#### 1. 处理单个模型

```bash
python process_model.py "模型文件夹路径"
```

例如：
```bash
python process_model.py "./1003_Tokai Teio"
```

## 🔧 功能特性

### 自动贴图识别
- 智能识别 `diff`、`base`、`shad_c` 等贴图文件
- 支持多种命名格式（如 `bdy` 和 `body`）
- 自动处理眼睛高光贴图

### 纹理处理流程
1. **阴影处理**：使用 base 贴图的红色通道作为阴影蒙版
2. **高光处理**：使用 base 贴图的绿色通道添加高光效果
3. **透明通道**：使用 base 贴图的蓝色通道设置透明度
4. **眼睛高光**：特殊处理眼睛的高光效果

### 智能优化
- 自动统一贴图尺寸
- 数值截断防止溢出
- 兼容不同 Pillow 版本

## 📊 处理结果

处理完成后，会在 `processed_results/` 文件夹中生成：

- `eye_final.png` - 最终眼睛贴图
- `face_final.png` - 最终面部贴图
- `hair_final.png` - 最终头发贴图
- `body_final.png` - 最终身体贴图
- `tail_final.png` - 最终尾巴贴图

## 🎨 技术细节

### 贴图通道说明

- **红色通道 (R)**：阴影蒙版
- **绿色通道 (G)**：高光蒙版
- **蓝色通道 (B)**：透明通道
- **Alpha 通道 (A)**：透明度

### 处理算法

1. **阴影合成**：`result = lerp(diff, shad_c, shadow_mask)`
2. **高光叠加**：`result = add(result, white * specular_mask)`
3. **透明设置**：`result.alpha = cutoff_mask`

## 🔍 故障排除

### 常见问题

1. **找不到贴图文件**
   - 确保模型文件夹包含 `Texture2D` 子文件夹
   - 检查贴图文件命名是否正确

2. **处理失败**
   - 运行 `check_textures.py` 分析贴图通道
   - 检查贴图文件是否损坏

3. **尺寸不匹配**
   - 程序会自动调整尺寸，但建议使用相同尺寸的贴图

## 📝 开发说明

### 代码结构

- `process_model.py`：核心处理逻辑
- `main.py`：特定模型的配置和处理
- `check_textures.py`：调试和分析工具

### 扩展功能

可以通过修改 `process_part` 函数的参数来：
- 调整阴影对比度
- 启用/禁用高光效果
- 启用/禁用透明通道

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

感谢 [Bilibili 上的技术文章](https://www.bilibili.com/opus/671644048083124224) 提供的处理流程参考，为项目开发提供了重要的技术指导。 
