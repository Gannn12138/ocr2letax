# OCR2LATEX 安装和配置指南

## 📋 系统要求

- Python 3.8 或更高版本
- 操作系统：Windows, macOS, Linux
- 内存：至少 2GB RAM
- 网络连接（用于Mathpix API调用）

## 🚀 快速开始

### 1. 安装Python依赖

```bash
# 进入项目目录
cd OCR2LATEX

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置Mathpix API

#### 2.1 注册Mathpix账户
1. 访问 [Mathpix官网](https://mathpix.com/)
2. 注册免费账户
3. 进入Dashboard获取API密钥

#### 2.2 配置API密钥
编辑 `src/config.py` 文件，替换以下内容：

```python
# 将这两行
MATHPIX_APP_ID = "your_app_id_here"
MATHPIX_APP_KEY = "your_app_key_here"

# 替换为您的实际密钥
MATHPIX_APP_ID = "your_actual_app_id"
MATHPIX_APP_KEY = "your_actual_app_key"
```

或者设置环境变量：

```bash
# Linux/macOS
export MATHPIX_APP_ID="your_actual_app_id"
export MATHPIX_APP_KEY="your_actual_app_key"

# Windows
set MATHPIX_APP_ID=your_actual_app_id
set MATHPIX_APP_KEY=your_actual_app_key
```

### 3. 测试运行

```bash
# 查看帮助信息
python main.py --help

# 处理示例图片（需要您提供图片）
python main.py path/to/your/image.jpg
```

## 📁 项目结构说明

```
OCR2LATEX/
├── src/                      # 核心代码模块
│   ├── __init__.py          # 包初始化
│   ├── config.py            # 配置文件 ⚠️ 需要配置API密钥
│   ├── image_processor.py   # 图像预处理
│   ├── mathpix_client.py    # Mathpix API客户端
│   └── result_processor.py  # 结果处理和输出
├── templates/               # HTML模板（自动生成）
├── uploads/                 # 上传图片目录
├── results/                 # 结果输出目录
├── main.py                  # 主程序入口
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
└── setup_guide.md          # 本安装指南
```

## 🔧 详细配置

### Mathpix API配置选项

在 `src/config.py` 中可以调整以下设置：

```python
# API配置
MATHPIX_API_URL = "https://api.mathpix.com/v3/text"  # API地址
OCR_CONFIDENCE_THRESHOLD = 0.7  # 置信度阈值
MAX_RETRIES = 3                 # 最大重试次数
TIMEOUT = 30                    # 请求超时时间

# 图像处理配置
MAX_IMAGE_SIZE = (2048, 2048)   # 最大图像尺寸
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf'}
```

### 日志配置

```python
# 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"
```

## 🎯 使用示例

### 基本用法

```bash
# 处理单张图片
python main.py math_problem.jpg

# 使用详细输出
python main.py math_problem.jpg --verbose
```

### 输出文件

处理完成后会在 `results/` 目录生成：

1. **JSON文件** (`image_name_result.json`)：
   - 完整的识别数据
   - 结构化的结果信息
   - 可用于程序进一步处理

2. **HTML文件** (`image_name_result.html`)：
   - 可视化的结果展示
   - LaTeX公式渲染
   - 用浏览器直接打开查看

### JSON结果格式

```json
{
  "metadata": {
    "version": "1.0",
    "created_time": "2024-11-06T10:30:00",
    "processor": "OCR2LATEX"
  },
  "image_info": {
    "filename": "math_problem.jpg",
    "original_size": [1920, 1080],
    "file_size": 245760
  },
  "ocr_result": {
    "success": true,
    "raw_text": "识别的文本内容",
    "latex_content": "LaTeX格式的数学公式",
    "confidence": 0.95,
    "processing_time": 2.3
  },
  "regions": [...],
  "analysis": {...}
}
```

## 🐛 常见问题

### 1. API密钥错误
**问题**：`API认证失败，请检查APP ID和APP KEY`

**解决**：
- 确认API密钥正确配置
- 检查网络连接
- 验证Mathpix账户状态

### 2. 图像格式不支持
**问题**：`不支持的图像格式`

**解决**：
- 支持格式：JPG, PNG, BMP, TIFF, PDF
- 转换图像格式后重试

### 3. 图像太大
**问题**：处理速度慢或内存不足

**解决**：
- 调整 `MAX_IMAGE_SIZE` 设置
- 压缩图像后处理

### 4. API配额用完
**问题**：`API配额已用完`

**解决**：
- Mathpix免费版每月1000次
- 等待下月重置或升级账户

### 5. 识别效果不佳
**问题**：识别准确率低

**建议**：
- 确保图像清晰、对比度高
- 避免倾斜和模糊
- 裁剪掉无关区域

## 📈 性能优化

### 图像预处理建议
1. **分辨率**：建议1000-2000像素宽度
2. **格式**：PNG格式通常效果更好
3. **对比度**：确保文字和背景对比明显
4. **角度**：尽量保持水平，避免倾斜

### API使用优化
1. **批量处理**：合理安排处理时间
2. **缓存结果**：避免重复处理相同图像
3. **错误处理**：网络异常时自动重试

## 🔒 安全注意事项

1. **API密钥保护**：
   - 不要将密钥提交到版本控制
   - 使用环境变量存储敏感信息

2. **图像隐私**：
   - 处理敏感内容时注意数据安全
   - 及时清理临时文件

## 🆘 获取帮助

如果遇到问题：

1. 查看日志文件 `ocr2latex.log`
2. 使用 `--verbose` 参数获取详细信息
3. 检查网络连接和API配额
4. 验证图像文件格式和质量

## 📝 更新日志

### v1.0.0 (2024-11-06)
- ✨ 初始版本发布
- 🖼️ 支持多种图像格式
- 🤖 集成Mathpix OCR API
- 📄 JSON和HTML结果输出
- 🔧 完整的图像预处理流程

