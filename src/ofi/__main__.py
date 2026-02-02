"""
OFI Research Pipeline - CLI Entry Point
一键运行完整的OFI可预测性分析
"""
import argparse
import sys
from pathlib import Path


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="OFI Research Pipeline - 自动化评估和报告生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整评估
  python -m src.ofi --config configs/data.yaml --universe configs/universe.yaml
  
  # 指定输出目录
  python -m src.ofi --outdir reports/new_run
  
  # 只运行质量检查
  python -m src.ofi --task quality_check
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="configs/data.yaml",
        help="数据配置文件路径"
    )
    
    parser.add_argument(
        "--universe",
        type=str,
        default="configs/universe.yaml",
        help="标的池配置文件路径"
    )
    
    parser.add_argument(
        "--outdir",
        type=str,
        default="reports",
        help="输出目录"
    )
    
    parser.add_argument(
        "--task",
        type=str,
        default="all",
        choices=["all", "quality_check", "ic_analysis", "model_eval", "robustness"],
        help="运行的任务类型"
    )
    
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        help="指定要分析的标的（可选，默认使用universe.yaml中的全部）"
    )
    
    parser.add_argument(
        "--start_date",
        type=str,
        help="开始日期 YYYY-MM-DD"
    )
    
    parser.add_argument(
        "--end_date",
        type=str,
        help="结束日期 YYYY-MM-DD"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    # 导入评估模块
    try:
        from .pipeline import run_all
    except ImportError:
        print("错误: 无法导入pipeline模块。请确保已安装包: pip install -e .")
        sys.exit(1)
    
    # 运行评估
    print("=" * 80)
    print("OFI Research Pipeline - Starting")
    print("=" * 80)
    print(f"Config: {args.config}")
    print(f"Universe: {args.universe}")
    print(f"Output: {args.outdir}")
    print(f"Task: {args.task}")
    print("=" * 80)
    
    try:
        run_all(
            config_path=args.config,
            universe_path=args.universe,
            outdir=args.outdir,
            task=args.task,
            symbols=args.symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            verbose=args.verbose
        )
        print("\n" + "=" * 80)
        print("Pipeline completed successfully!")
        print(f"Results saved to: {args.outdir}")
        print("=" * 80)
    except Exception as e:
        print(f"\n错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
