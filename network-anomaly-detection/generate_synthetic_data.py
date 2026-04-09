#!/usr/bin/env python3
"""
Generate synthetic data for network anomaly detection.
Expands the dataset to enable proper model training with class balancing.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

def generate_synthetic_data(original_df: pd.DataFrame, target_samples: int = 5000) -> pd.DataFrame:
    """Generate synthetic data based on original distribution."""
    
    print(f"Original dataset: {len(original_df)} samples")
    print(f"Label distribution:\n{original_df['label'].value_counts()}\n")
    
    # Separate by label
    labels = original_df['label'].unique()
    synthetic_data = []
    
    # Get feature columns (excluding label)
    feature_cols = original_df.drop(columns=['label']).columns
    
    samples_per_label = target_samples // len(labels)
    
    for label in labels:
        label_data = original_df[original_df['label'] == label].drop(columns=['label'])
        
        print(f"Generating {samples_per_label} samples for label {label}...")
        
        # Get statistics from real samples
        means = label_data.mean().values
        stds = label_data.std().values
        
        # Generate synthetic samples
        n_generate = samples_per_label - len(label_data)
        
        synthetic_samples = np.random.normal(
            loc=means,
            scale=stds,
            size=(n_generate, len(feature_cols))
        )
        
        # Convert to DataFrame
        synthetic_df = pd.DataFrame(synthetic_samples, columns=feature_cols)
        synthetic_df['label'] = label
        
        # Combine with original
        combined = pd.concat([label_data.copy(), synthetic_df], ignore_index=True)
        combined['label'] = label
        synthetic_data.append(combined)
    
    # Combine all labels
    result_df = pd.concat(synthetic_data, ignore_index=True)
    
    # Shuffle
    result_df = result_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"\nGenerated dataset: {len(result_df)} samples")
    print(f"Label distribution:\n{result_df['label'].value_counts()}\n")
    
    return result_df


def main():
    # Load original data
    original_path = 'network-anomaly-detection/data/processed/processed.csv'
    df = pd.read_csv(original_path)
    
    # Generate synthetic data
    synthetic_df = generate_synthetic_data(df, target_samples=5000)
    
    # Save
    output_path = 'network-anomaly-detection/data/processed/processed_expanded.csv'
    synthetic_df.to_csv(output_path, index=False)
    print(f"Saved to: {output_path}")


if __name__ == '__main__':
    main()
