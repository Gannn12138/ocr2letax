# OCR2LATEX - 数学题目识别系统 (MVP版本)

## 项目简介

一个简单的数学题目图像识别工具，能够将包含中文文字和数学公式的图片转换为LaTeX格式。

## 功能特点

- 🖼️ 支持常见图片格式 (JPG, PNG, PDF等)
- 🔍 智能图像预处理和优化
- 🧮 基于Mathpix API的高精度OCR识别
- 📄 JSON格式结果存储
- 🌐 HTML可视化查看器

## 系统架构 (简化版)

```
图片输入 → 图像预处理 → Mathpix API → 结果处理 → JSON输出 → HTML展示
```

## 项目结构

```
OCR2LATEX/
├── src/
│   ├── image_processor.py      # 图像预处理模块
│   ├── mathpix_client.py       # Mathpix API客户端
│   ├── result_processor.py     # 结果处理模块
│   └── config.py              # 配置文件
├── templates/
│   └── result_viewer.html     # 结果查看器模板
├── uploads/                   # 上传图片目录
├── results/                   # 结果JSON目录
├── main.py                    # 主处理脚本
├── requirements.txt           # Python依赖
└── README.md                  # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

在 `src/config.py` 中设置您的Mathpix API密钥：

```python
MATHPIX_APP_ID = "your_app_id"
MATHPIX_APP_KEY = "your_app_key"
```

### 3. 运行识别

```bash
python main.py path/to/your/image.jpg
```

### 4. 查看结果

运行后会生成：

- `results/image_name_result.json` - 识别结果
- `results/image_name_result.html` - 可视化页面

直接用浏览器打开HTML文件即可查看识别结果。

## 输出格式

### JSON结构

```json
{
  "image_info": {
    "filename": "example.jpg",
    "size": [1920, 1080],
    "processed_time": "2024-11-06T10:30:00"
  },
  "ocr_result": {
    "raw_text": "原始识别文本",
    "latex_content": "LaTeX格式内容",
    "confidence": 0.95,
    "processing_time": 2.3
  },
  "regions": [
    {
      "type": "text",
      "content": "题目文字部分",
      "bbox": [x, y, width, height]
    },
    {
      "type": "formula", 
      "content": "\\frac{x^2}{2}",
      "bbox": [x, y, width, height]
    }
  ]
}
```

## 技术栈

- **Python 3.8+** - 主要开发语言
- **OpenCV** - 图像处理
- **Pillow** - 图像操作
- **requests** - HTTP客户端
- **Mathpix API** - OCR识别服务

## 注意事项

- Mathpix免费版每月限制1000次调用
- 建议图片分辨率不超过2048x2048
- 支持中文和数学公式混合识别

## 后续扩展计划

- [ ] 批量处理功能
- [ ] Web界面
- [ ] 本地OCR备选方案
- [ ] 结果编辑功能
