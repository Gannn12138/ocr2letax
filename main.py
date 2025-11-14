#!/usr/bin/env python3
"""
OCR2LATEX 主处理脚本
用法: python main.py <image_path>
"""

import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import LOG_LEVEL, LOG_FORMAT
from src.image_processor import image_processor
from src.mathpix_client import mathpix_client
from src.result_processor import result_processor


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ocr2latex.log', encoding='utf-8')
        ]
    )


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                        OCR2LATEX                             ║
║                   数学题目识别系统                            ║
║                                                              ║
║  🖼️  图像识别  →  🔍 OCR处理  →  📄 LaTeX输出              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_image_path(image_path: str) -> bool:
    """
    验证图像路径
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        路径是否有效
    """
    path = Path(image_path)
    
    if not path.exists():
        print(f"❌ 错误: 文件不存在 - {image_path}")
        return False
    
    if not path.is_file():
        print(f"❌ 错误: 不是有效文件 - {image_path}")
        return False
    
    # 检查文件扩展名
    from src.config import SUPPORTED_FORMATS
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"❌ 错误: 不支持的文件格式 - {path.suffix}")
        print(f"支持的格式: {', '.join(SUPPORTED_FORMATS)}")
        return False
    
    return True


def process_image(image_path: str) -> dict:
    """
    处理单张图像
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        处理结果
    """
    logger = logging.getLogger(__name__)
    
    print(f"\n🔄 开始处理图像: {Path(image_path).name}")
    print("=" * 60)
    
    try:
        # 步骤1: 获取图像信息
        print("📋 步骤 1/5: 获取图像信息...")
        image_info = image_processor.get_image_info(image_path)
        if not image_info:
            return {'success': False, 'error': '无法获取图像信息'}
        
        print(f"   ✅ 图像尺寸: {image_info['size'][0]} × {image_info['size'][1]}")
        print(f"   ✅ 文件大小: {image_info['file_size'] / 1024:.1f} KB")
        print(f"   ✅ 图像格式: {image_info['format']}")
        
        # 步骤2: 图像预处理
        print("\n🔧 步骤 2/5: 图像预处理...")
        preprocess_result = image_processor.preprocess_image(image_path)
        if preprocess_result is None:
            return {'success': False, 'error': '图像预处理失败'}
        
        processed_image, process_info = preprocess_result
        print(f"   ✅ 预处理完成: {' → '.join(process_info['preprocessing_steps'])}")
        
        # 步骤3: 转换为base64
        print("\n📦 步骤 3/5: 图像编码...")
        image_base64 = image_processor.image_to_base64(processed_image)
        if not image_base64:
            return {'success': False, 'error': '图像编码失败'}
        
        print(f"   ✅ Base64编码完成: {len(image_base64)} 字符")
        
        # 步骤4: OCR识别
        print("\n🤖 步骤 4/5: OCR识别...")
        
        # 检查API凭证
        if not mathpix_client.check_credentials():
            return {'success': False, 'error': 'Mathpix API凭证未配置或无效'}
        
        # 显示API使用信息
        usage_info = mathpix_client.get_usage_info()
        print(f"   📊 API使用情况: {usage_info['usage_count']}/1000 (剩余: {usage_info['remaining']})")
        
        # 执行OCR
        ocr_result = mathpix_client.process_image(image_base64)
        
        if not ocr_result['success']:
            error_msg = ocr_result.get('error', '未知错误')
            print(f"   ❌ OCR识别失败: {error_msg}")
            return {'success': False, 'error': f'OCR识别失败: {error_msg}'}
        
        print(f"   ✅ OCR识别成功!")
        print(f"   📊 置信度: {ocr_result['confidence']:.2%}")
        print(f"   ⏱️  处理时间: {ocr_result['processing_time']:.2f}秒")
        print(f"   📝 识别字符: {len(ocr_result['raw_text'])} 个")
        
        # 步骤5: 保存结果
        print("\n💾 步骤 5/5: 保存结果...")
        
        save_result = result_processor.process_and_save_results(
            image_info, ocr_result, process_info
        )
        
        if not save_result['success']:
            return {'success': False, 'error': f"保存结果失败: {save_result.get('error', '未知错误')}"}
        
        print(f"   ✅ JSON结果: {save_result['json_path']}")
        print(f"   ✅ HTML页面: {save_result['html_path']}")
        
        return {
            'success': True,
            'image_info': image_info,
            'ocr_result': ocr_result,
            'save_result': save_result
        }
        
    except Exception as e:
        logger.error(f"处理图像时发生异常: {e}", exc_info=True)
        return {'success': False, 'error': f'处理异常: {str(e)}'}


def print_results_summary(result: dict):
    """
    打印结果摘要
    
    Args:
        result: 处理结果
    """
    if not result['success']:
        print(f"\n❌ 处理失败: {result['error']}")
        return
    
    ocr_result = result['ocr_result']
    save_result = result['save_result']
    
    print("\n" + "=" * 60)
    print("🎉 处理完成! 结果摘要:")
    print("=" * 60)
    
    # 识别结果预览
    raw_text = ocr_result['raw_text']
    if len(raw_text) > 100:
        text_preview = raw_text[:100] + "..."
    else:
        text_preview = raw_text
    
    print(f"📝 识别文本预览:")
    print(f"   {text_preview}")
    
    if ocr_result['latex_content']:
        latex_content = ocr_result['latex_content']
        if len(latex_content) > 100:
            latex_preview = latex_content[:100] + "..."
        else:
            latex_preview = latex_content
        
        print(f"\n🔬 LaTeX内容预览:")
        print(f"   {latex_preview}")
    
    print(f"\n📊 统计信息:")
    print(f"   • 置信度: {ocr_result['confidence']:.2%}")
    print(f"   • 处理时间: {ocr_result['processing_time']:.2f}秒")
    print(f"   • 字符数量: {len(raw_text)}")
    print(f"   • 区域数量: {len(ocr_result.get('regions', []))}")
    
    print(f"\n📁 输出文件:")
    print(f"   • JSON: {save_result['json_path']}")
    print(f"   • HTML: {save_result['html_path']}")
    
    print(f"\n💡 提示:")
    print(f"   • 用浏览器打开HTML文件查看可视化结果")
    print(f"   • JSON文件包含完整的识别数据")


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 打印横幅
    print_banner()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='OCR2LATEX - 数学题目图像识别系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py image.jpg              # 处理单张图片
  python main.py /path/to/math.png      # 使用绝对路径
  python main.py --help                 # 显示帮助信息

支持的图像格式: JPG, PNG, BMP, TIFF, PDF
        """
    )
    
    parser.add_argument(
        'image_path',
        help='要处理的图像文件路径'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志信息'
    )
    
    # 检查参数
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # 设置详细日志
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 验证图像路径
    if not validate_image_path(args.image_path):
        sys.exit(1)
    
    # 记录开始时间
    start_time = datetime.now()
    logger.info(f"开始处理图像: {args.image_path}")
    
    try:
        # 处理图像
        result = process_image(args.image_path)
        
        # 打印结果摘要
        print_results_summary(result)
        
        # 记录结束时间
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        if result['success']:
            print(f"\n✨ 总处理时间: {total_time:.2f}秒")
            logger.info(f"图像处理成功完成，总耗时: {total_time:.2f}秒")
            sys.exit(0)
        else:
            logger.error(f"图像处理失败: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        logger.info("用户中断操作")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        logger.error(f"程序异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

