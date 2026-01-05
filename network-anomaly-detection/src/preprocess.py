#!/usr/bin/env python3
"""
Network Anomaly Detection - Data Preprocessing Pipeline

This script implements a comprehensive data preprocessing pipeline for network flow data.
It handles data cleaning, feature encoding, scaling, and optional dimensionality reduction.

Features:
- Automatic data generation if input file is missing
- Duplicate removal and missing value handling
- Categorical encoding (label encoding or one-hot encoding)
- Numeric feature scaling with StandardScaler
- Optional PCA for dimensionality reduction
- Model persistence (scalers and encoders)
- Comprehensive logging and validation

Usage:
    python src/preprocess.py --input data/raw/sample.csv --output data/processed/processed.csv
    python src/preprocess.py --input data/raw/sample.csv --pca --dry-run
    python src/preprocess.py  # Auto-generates sample data if input missing
"""

import argparse
import pandas as pd
import numpy as np
import logging
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import joblib
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.decomposition import PCA
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('preprocessing.log')
    ]
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class NetworkDataPreprocessor:
    """
    Comprehensive data preprocessor for network anomaly detection.
    
    This class handles the complete preprocessing pipeline including data cleaning,
    feature encoding, scaling, and optional dimensionality reduction.
    """
    
    def __init__(self, use_pca: bool = False, pca_components: Optional[int] = None):
        """
        Initialize the preprocessor.
        
        Args:
            use_pca (bool): Whether to apply PCA dimensionality reduction
            pca_components (int, optional): Number of PCA components. If None, 
                                          uses 95% variance explained
        """
        self.use_pca = use_pca
        self.pca_components = pca_components
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.onehot_encoder = None
        self.pca = None
        self.feature_names = None
        self.categorical_columns = []
        self.numeric_columns = []
        
        logger.info(f"Initialized preprocessor with PCA: {use_pca}")
    
    def auto_generate_data(self, output_path: str) -> str:
        """
        Automatically generate sample data if input file is missing.
        
        Args:
            output_path (str): Path where to save generated data
            
        Returns:
            str: Path to the generated data file
        """
        logger.info("Input file missing, auto-generating sample data...")
        
        try:
            # Run the synthetic data generator
            cmd = [
                sys.executable, 
                "src/synthetic_data.py", 
                "--rows", "1000", 
                "--output", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Successfully generated sample data")
            logger.debug(f"Generator output: {result.stdout}")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate sample data: {e}")
            logger.error(f"Error output: {e.stderr}")
            raise RuntimeError("Could not auto-generate sample data")
    
    def load_data(self, input_path: str) -> pd.DataFrame:
        """
        Load data from CSV file with automatic generation fallback.
        
        Args:
            input_path (str): Path to input CSV file
            
        Returns:
            pd.DataFrame: Loaded data
        """
        input_file = Path(input_path)
        
        if not input_file.exists():
            logger.warning(f"Input file {input_path} not found")
            # Auto-generate data in the same directory
            generated_path = input_file.parent / "sample.csv"
            input_path = self.auto_generate_data(str(generated_path))
            input_file = Path(input_path)
        
        logger.info(f"Loading data from {input_file}")
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(input_file, encoding=encoding)
                    logger.info(f"Successfully loaded data with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # Last resort: ignore encoding errors
                df = pd.read_csv(input_file, encoding='utf-8', encoding_errors='ignore')
                logger.warning("Loaded data with encoding errors ignored")
            
            logger.info(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def identify_column_types(self, df: pd.DataFrame) -> Tuple[list, list]:
        """
        Identify categorical and numeric columns.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            Tuple[list, list]: (categorical_columns, numeric_columns)
        """
        categorical_cols = []
        numeric_cols = []
        
        for col in df.columns:
            if col.lower() in ['label', 'target', 'class']:
                # Skip target column
                continue
            elif df[col].dtype == 'object' or df[col].nunique() < 20:
                categorical_cols.append(col)
            else:
                numeric_cols.append(col)
        
        logger.info(f"Identified {len(categorical_cols)} categorical columns: {categorical_cols}")
        logger.info(f"Identified {len(numeric_cols)} numeric columns: {numeric_cols}")
        
        return categorical_cols, numeric_cols
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the dataset by removing duplicates and handling missing values.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Cleaned dataframe
        """
        logger.info("Starting data cleaning...")
        original_shape = df.shape
        
        # Remove duplicates
        df_cleaned = df.drop_duplicates()
        duplicates_removed = original_shape[0] - df_cleaned.shape[0]
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate rows")
        
        # Handle missing values
        missing_before = df_cleaned.isnull().sum().sum()
        if missing_before > 0:
            logger.info(f"Found {missing_before} missing values")
            
            # Fill numeric columns with median
            numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_cleaned[col].isnull().sum() > 0:
                    median_val = df_cleaned[col].median()
                    df_cleaned[col].fillna(median_val, inplace=True)
                    logger.debug(f"Filled {col} with median: {median_val}")
            
            # Fill categorical columns with mode
            categorical_cols = df_cleaned.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                if df_cleaned[col].isnull().sum() > 0:
                    mode_val = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Unknown'
                    df_cleaned[col].fillna(mode_val, inplace=True)
                    logger.debug(f"Filled {col} with mode: {mode_val}")
        
        logger.info(f"Data cleaning completed. Final shape: {df_cleaned.shape}")
        return df_cleaned
    
    def encode_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Encode categorical features using label encoding or one-hot encoding.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Dataframe with encoded features
        """
        logger.info("Starting feature encoding...")
        df_encoded = df.copy()
        
        # Identify column types
        self.categorical_columns, self.numeric_columns = self.identify_column_types(df)
        
        # Handle target column separately
        target_col = None
        if 'label' in df.columns:
            target_col = 'label'
        elif 'target' in df.columns:
            target_col = 'target'
        elif 'class' in df.columns:
            target_col = 'class'
        
        if target_col:
            # Label encode target column
            self.label_encoders[target_col] = LabelEncoder()
            df_encoded[target_col] = self.label_encoders[target_col].fit_transform(df[target_col])
            logger.info(f"Label encoded target column: {target_col}")
            logger.info(f"Target classes: {self.label_encoders[target_col].classes_}")
        
        # Encode categorical features
        for col in self.categorical_columns:
            if col == target_col:
                continue
                
            unique_values = df[col].nunique()
            if unique_values <= 10:  # Use one-hot encoding for low cardinality
                if self.onehot_encoder is None:
                    self.onehot_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
                    onehot_cols = [col]
                else:
                    onehot_cols.append(col)
                logger.debug(f"Prepared {col} for one-hot encoding ({unique_values} unique values)")
            else:  # Use label encoding for high cardinality
                self.label_encoders[col] = LabelEncoder()
                df_encoded[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                logger.debug(f"Label encoded {col} ({unique_values} unique values)")
        
        # Apply one-hot encoding if needed
        if self.onehot_encoder is not None:
            onehot_data = self.onehot_encoder.fit_transform(df[onehot_cols])
            onehot_feature_names = self.onehot_encoder.get_feature_names_out(onehot_cols)
            
            # Create dataframe with one-hot encoded features
            onehot_df = pd.DataFrame(onehot_data, columns=onehot_feature_names, index=df.index)
            
            # Remove original categorical columns and add one-hot encoded ones
            df_encoded = df_encoded.drop(columns=onehot_cols)
            df_encoded = pd.concat([df_encoded, onehot_df], axis=1)
            
            logger.info(f"One-hot encoded {len(onehot_cols)} columns: {onehot_cols}")
        
        logger.info(f"Feature encoding completed. Final shape: {df_encoded.shape}")
        return df_encoded
    
    def scale_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Scale numeric features using StandardScaler.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Dataframe with scaled features
        """
        logger.info("Starting feature scaling...")
        
        # Identify numeric columns (excluding target)
        target_cols = ['label', 'target', 'class']
        numeric_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                       if col not in target_cols]
        
        if not numeric_cols:
            logger.warning("No numeric columns found for scaling")
            return df
        
        # Fit scaler and transform
        df_scaled = df.copy()
        scaled_features = self.scaler.fit_transform(df[numeric_cols])
        
        # Replace original columns with scaled values
        df_scaled[numeric_cols] = scaled_features
        
        self.feature_names = numeric_cols
        logger.info(f"Scaled {len(numeric_cols)} numeric features")
        
        return df_scaled
    
    def apply_pca(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply PCA dimensionality reduction if enabled.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Dataframe with PCA-transformed features
        """
        if not self.use_pca:
            return df
        
        logger.info("Applying PCA dimensionality reduction...")
        
        # Get numeric features (excluding target)
        target_cols = ['label', 'target', 'class']
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                       if col not in target_cols]
        
        if not feature_cols:
            logger.warning("No features found for PCA")
            return df
        
        # Determine number of components
        if self.pca_components is None:
            # Use 95% variance explained
            self.pca = PCA(n_components=0.95)
        else:
            self.pca = PCA(n_components=self.pca_components)
        
        # Fit and transform
        pca_features = self.pca.fit_transform(df[feature_cols])
        
        # Create new dataframe with PCA features
        pca_columns = [f'PC_{i+1}' for i in range(pca_features.shape[1])]
        pca_df = pd.DataFrame(pca_features, columns=pca_columns, index=df.index)
        
        # Combine with non-feature columns
        non_feature_cols = [col for col in df.columns if col not in feature_cols]
        df_pca = pd.concat([df[non_feature_cols], pca_df], axis=1)
        
        explained_variance = self.pca.explained_variance_ratio_.sum()
        logger.info(f"PCA completed: {pca_features.shape[1]} components, "
                   f"{explained_variance:.3f} variance explained")
        
        return df_pca
    
    def save_models(self, models_dir: str = "models"):
        """
        Save preprocessing models (scalers, encoders) to disk.
        
        Args:
            models_dir (str): Directory to save models
        """
        models_path = Path(models_dir)
        models_path.mkdir(exist_ok=True)
        
        logger.info(f"Saving preprocessing models to {models_path}")
        
        # Save scaler
        if self.scaler is not None:
            scaler_path = models_path / "scaler.joblib"
            joblib.dump(self.scaler, scaler_path)
            logger.info(f"Saved scaler to {scaler_path}")
        
        # Save label encoders
        for col, encoder in self.label_encoders.items():
            encoder_path = models_path / f"label_encoder_{col}.joblib"
            joblib.dump(encoder, encoder_path)
            logger.info(f"Saved label encoder for {col} to {encoder_path}")
        
        # Save one-hot encoder
        if self.onehot_encoder is not None:
            onehot_path = models_path / "onehot_encoder.joblib"
            joblib.dump(self.onehot_encoder, onehot_path)
            logger.info(f"Saved one-hot encoder to {onehot_path}")
        
        # Save PCA
        if self.pca is not None:
            pca_path = models_path / "pca.joblib"
            joblib.dump(self.pca, pca_path)
            logger.info(f"Saved PCA to {pca_path}")
        
        # Save feature names
        if self.feature_names is not None:
            features_path = models_path / "feature_names.joblib"
            joblib.dump(self.feature_names, features_path)
            logger.info(f"Saved feature names to {features_path}")
    
    def preprocess(self, input_path: str, output_path: str, dry_run: bool = False) -> pd.DataFrame:
        """
        Run the complete preprocessing pipeline.
        
        Args:
            input_path (str): Path to input CSV file
            output_path (str): Path to save processed CSV file
            dry_run (bool): If True, don't save files
            
        Returns:
            pd.DataFrame: Processed dataframe
        """
        logger.info("Starting preprocessing pipeline...")
        
        # Load data
        df = self.load_data(input_path)
        
        # Clean data
        df_cleaned = self.clean_data(df)
        
        # Encode features
        df_encoded = self.encode_features(df_cleaned)
        
        # Scale features
        df_scaled = self.scale_features(df_encoded)
        
        # Apply PCA if enabled
        df_final = self.apply_pca(df_scaled)
        
        # Save processed data
        if not dry_run:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            df_final.to_csv(output_file, index=False)
            logger.info(f"Saved processed data to {output_file}")
            
            # Save models
            self.save_models()
        
        logger.info("Preprocessing pipeline completed successfully")
        return df_final


def validate_output(df: pd.DataFrame, output_path: str) -> None:
    """
    Perform inline unit checks on the processed data.
    
    Args:
        df (pd.DataFrame): Processed dataframe
        output_path (str): Path to saved file
    """
    logger.info("Performing validation checks...")
    
    # Check file exists and is readable
    output_file = Path(output_path)
    if not output_file.exists():
        logger.error(f"Output file {output_path} was not created")
        return
    
    # Load and verify the saved file
    try:
        saved_df = pd.read_csv(output_path)
        logger.info(f"[OK] File validation: {saved_df.shape[0]} rows, {saved_df.shape[1]} columns")
        
        # Print sample rows
        logger.info("[INFO] Sample of processed data (first 3 rows):")
        print("\n" + "="*80)
        print("PROCESSED DATA SAMPLE:")
        print("="*80)
        print(saved_df.head(3).to_string())
        print("="*80)
        
        # Check for missing values
        missing_count = saved_df.isnull().sum().sum()
        if missing_count == 0:
            logger.info("[OK] No missing values found")
        else:
            logger.warning(f"[WARN] Found {missing_count} missing values")
        
        # Check data types
        numeric_cols = saved_df.select_dtypes(include=[np.number]).shape[1]
        logger.info(f"[OK] Numeric columns: {numeric_cols}")
        
        # Check for infinite values
        inf_count = np.isinf(saved_df.select_dtypes(include=[np.number])).sum().sum()
        if inf_count == 0:
            logger.info("[OK] No infinite values found")
        else:
            logger.warning(f"[WARN] Found {inf_count} infinite values")
            
    except Exception as e:
        logger.error(f"[ERROR] Validation failed: {e}")


def main():
    """
    Main function to run the preprocessing pipeline from command line.
    """
    parser = argparse.ArgumentParser(
        description="Network Anomaly Detection - Data Preprocessing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/preprocess.py --input data/raw/sample.csv --output data/processed/processed.csv
  python src/preprocess.py --input data/raw/sample.csv --pca --dry-run
  python src/preprocess.py  # Auto-generates sample data if input missing
  python src/preprocess.py --input data/raw/large_dataset.csv --output data/processed/large_processed.csv --pca --pca-components 50
        """
    )
    
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/raw/sample.csv',
        help='Path to input CSV file (default: data/raw/sample.csv)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/processed.csv',
        help='Path to output processed CSV file (default: data/processed/processed.csv)'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Run preprocessing without saving files'
    )
    
    parser.add_argument(
        '--pca', 
        action='store_true',
        help='Apply PCA dimensionality reduction'
    )
    
    parser.add_argument(
        '--pca-components', 
        type=int, 
        default=None,
        help='Number of PCA components (default: auto-determine for 95% variance)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize preprocessor
        preprocessor = NetworkDataPreprocessor(
            use_pca=args.pca,
            pca_components=args.pca_components
        )
        
        # Run preprocessing pipeline
        processed_df = preprocessor.preprocess(
            input_path=args.input,
            output_path=args.output,
            dry_run=args.dry_run
        )
        
        # Perform validation
        if not args.dry_run:
            validate_output(processed_df, args.output)
        
        logger.info("[SUCCESS] Preprocessing completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"[ERROR] Preprocessing failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
