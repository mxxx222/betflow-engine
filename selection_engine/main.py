#!/usr/bin/env python3
"""
Selection Engine Main Runner
Orchestrates data pipeline, model training, and live deployment
"""
import asyncio
import logging
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from data_pipeline import SelectionEngineDataPipeline
from model_training import SelectionEngineModel, ModelEvaluator
from selection_logic import SelectionEngine, SelectionCriteria
from backtesting import SelectionEngineBacktester
from live_pipeline import LivePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelectionEngineRunner:
    """Main runner for selection engine"""
    
    def __init__(self):
        self.data_pipeline = SelectionEngineDataPipeline()
        self.model_trainer = SelectionEngineModel()
        self.evaluator = ModelEvaluator()
        self.selection_engine = SelectionEngine(SelectionCriteria())
        self.backtester = SelectionEngineBacktester(self.selection_engine)
        
    async def run_full_pipeline(self):
        """Run complete selection engine pipeline"""
        logger.info("🚀 Starting Selection Engine Pipeline")
        
        # Step 1: Build dataset
        logger.info("📊 Step 1: Building dataset...")
        df = await self.data_pipeline.build_dataset()
        logger.info(f"✅ Dataset built: {len(df)} matches")
        
        # Step 2: Train models
        logger.info("🧠 Step 2: Training models...")
        training_results = self.model_trainer.train_models(df)
        logger.info(f"✅ Models trained: {len(training_results)} model combinations")
        
        # Step 3: Evaluate models
        logger.info("📈 Step 3: Evaluating models...")
        evaluation_results = self.evaluator.evaluate_models(df, self.model_trainer.models)
        logger.info("✅ Model evaluation complete")
        
        # Step 4: Run backtest
        logger.info("🧪 Step 4: Running backtest...")
        start_date = datetime(2023, 8, 1)
        end_date = datetime(2024, 5, 31)
        backtest_results = self.backtester.run_backtest(df, start_date, end_date)
        
        if backtest_results:
            logger.info(f"✅ Backtest complete: {backtest_results.overall_roi:.2%} ROI, {backtest_results.overall_hit_rate:.1%} hit rate")
            
            # Generate report
            report = self.backtester.generate_report(backtest_results)
            with open('selection_engine/final_report.md', 'w') as f:
                f.write(report)
            logger.info("📄 Report saved to selection_engine/final_report.md")
        
        # Step 5: Save models
        logger.info("💾 Step 5: Saving models...")
        self.model_trainer.save_models('selection_engine/models.pkl')
        logger.info("✅ Models saved")
        
        logger.info("🎯 Selection Engine Pipeline Complete!")
        return df, backtest_results
    
    async def run_data_pipeline_only(self):
        """Run only data pipeline"""
        logger.info("📊 Running data pipeline...")
        df = await self.data_pipeline.build_dataset()
        df.to_csv('selection_engine/dataset.csv', index=False)
        logger.info(f"✅ Dataset saved: {len(df)} matches")
        return df
    
    async def run_model_training_only(self):
        """Run only model training"""
        logger.info("🧠 Running model training...")
        
        # Load dataset
        import pandas as pd
        df = pd.read_csv('selection_engine/dataset.csv')
        
        # Train models
        training_results = self.model_trainer.train_models(df)
        
        # Evaluate models
        evaluation_results = self.evaluator.evaluate_models(df, self.model_trainer.models)
        
        # Save models
        self.model_trainer.save_models('selection_engine/models.pkl')
        
        logger.info("✅ Model training complete")
        return training_results, evaluation_results
    
    async def run_backtest_only(self):
        """Run only backtesting"""
        logger.info("🧪 Running backtest...")
        
        # Load dataset
        import pandas as pd
        df = pd.read_csv('selection_engine/dataset.csv')
        df['date'] = pd.to_datetime(df['date'])
        
        # Load models
        self.model_trainer.load_models('selection_engine/models.pkl')
        self.selection_engine.load_models(self.model_trainer.models)
        
        # Run backtest
        start_date = datetime(2023, 8, 1)
        end_date = datetime(2024, 5, 31)
        results = self.backtester.run_backtest(df, start_date, end_date)
        
        if results:
            # Generate report
            report = self.backtester.generate_report(results)
            with open('selection_engine/backtest_report.md', 'w') as f:
                f.write(report)
            
            # Plot performance
            self.backtester.plot_performance(results, 'selection_engine/performance_plots.png')
            
            logger.info(f"✅ Backtest complete: {results.overall_roi:.2%} ROI")
        
        return results
    
    async def run_live_pipeline(self):
        """Run live pipeline for production"""
        logger.info("🚀 Starting live pipeline...")
        
        # Load models
        self.model_trainer.load_models('selection_engine/models.pkl')
        
        # Initialize live pipeline
        API_URL = "https://betflow-api.onrender.com"
        WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        
        pipeline = LivePipeline(API_URL, WEBHOOK_URL)
        await pipeline.run()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Selection Engine Runner')
    parser.add_argument('--mode', choices=['full', 'data', 'train', 'backtest', 'live'], 
                       default='full', help='Pipeline mode to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = SelectionEngineRunner()
    
    if args.mode == 'full':
        asyncio.run(runner.run_full_pipeline())
    elif args.mode == 'data':
        asyncio.run(runner.run_data_pipeline_only())
    elif args.mode == 'train':
        asyncio.run(runner.run_model_training_only())
    elif args.mode == 'backtest':
        asyncio.run(runner.run_backtest_only())
    elif args.mode == 'live':
        asyncio.run(runner.run_live_pipeline())


if __name__ == "__main__":
    main()
