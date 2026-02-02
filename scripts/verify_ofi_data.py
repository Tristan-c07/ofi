"""
验证重新生成的 OFI 数据是否正确
"""
import pandas as pd
from pathlib import Path
import random

def check_ofi_file(file_path: Path) -> dict:
    """检查单个 OFI 文件"""
    df = pd.read_parquet(file_path)
    
    return {
        'file': file_path.name,
        'symbol': file_path.parent.name,
        'shape': df.shape,
        'n_minutes': df.shape[0],
        'time_start': df.index[0] if len(df) > 0 else None,
        'time_end': df.index[-1] if len(df) > 0 else None,
        'is_valid': df.shape[0] > 1 and df.index[0].year >= 2020,
        'columns': df.columns.tolist()
    }

def main():
    ofi_dir = Path("data/features/ofi_minute")
    
    # 收集所有文件
    all_files = list(ofi_dir.glob("*/*.parquet"))
    print(f"Total OFI files: {len(all_files)}")
    
    # 随机抽样检查
    sample_size = min(10, len(all_files))
    sample_files = random.sample(all_files, sample_size)
    
    print(f"\nChecking {sample_size} random files:\n")
    
    valid_count = 0
    invalid_count = 0
    
    for f in sample_files:
        result = check_ofi_file(f)
        status = "✓" if result['is_valid'] else "✗"
        print(f"{status} {result['symbol']}/{result['file']}")
        print(f"  Shape: {result['shape']}, Time: {result['time_start']} to {result['time_end']}")
        
        if result['is_valid']:
            valid_count += 1
        else:
            invalid_count += 1
    
    print(f"\n{'='*60}")
    print(f"Valid: {valid_count}/{sample_size}")
    print(f"Invalid: {invalid_count}/{sample_size}")
    print(f"{'='*60}")
    
    # 检查特定文件（之前有问题的）
    print("\nChecking previously problematic file:")
    problem_file = ofi_dir / "510050.XSHG" / "2021-01-04.parquet"
    if problem_file.exists():
        result = check_ofi_file(problem_file)
        status = "✓" if result['is_valid'] else "✗"
        print(f"{status} {result['symbol']}/{result['file']}")
        print(f"  Shape: {result['shape']}, Time: {result['time_start']} to {result['time_end']}")
        print(f"  Columns: {result['columns']}")
    else:
        print("  File not found!")

if __name__ == "__main__":
    main()
