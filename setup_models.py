"""
Download and setup all required ML models
Run this ONCE after installing requirements: python setup_models.py
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelSetup:
    """Download and setup all ML models"""
    
    def __init__(self):
        self.models_dir = 'python_backend/models'
        os.makedirs(self.models_dir, exist_ok=True)
    
    def setup_all(self):
        """Setup all required models"""
        logger.info("=" * 60)
        logger.info("AI TENNIS COACH - MODEL SETUP")
        logger.info("=" * 60)
        
        # 1. Download YOLO (optional - for player detection)
        self.setup_yolo()
        
        # 2. Verify setup
        self.verify_setup()
        
        logger.info("=" * 60)
        logger.info("✅ SETUP COMPLETE!")
        logger.info("=" * 60)
    
    def setup_yolo(self):
        """Download YOLOv8 model for player detection (optional)"""
        logger.info("\n📥 Setting up YOLOv8 (Optional - Player Detection)...")
        
        yolo_path = os.path.join(self.models_dir, 'yolov8n.pt')
        
        if os.path.exists(yolo_path):
            logger.info("   ✅ YOLOv8 already downloaded")
            return
        
        try:
            from ultralytics import YOLO
            
            # YOLOv8 will auto-download on first use
            logger.info("   Downloading YOLOv8 nano model (~6MB)...")
            model = YOLO('yolov8n.pt')
            
            # Move to models directory
            if os.path.exists('yolov8n.pt'):
                import shutil
                shutil.move('yolov8n.pt', yolo_path)
            
            logger.info("   ✅ YOLOv8 downloaded successfully")
            logger.info(f"   Model size: {os.path.getsize(yolo_path) / 1024 / 1024:.1f} MB")
            
        except ImportError:
            logger.warning("   ⚠️  ultralytics not installed - skipping YOLO download")
            logger.info("   To install: pip install ultralytics torch torchvision")
        except Exception as e:
            logger.error(f"   ❌ Error downloading YOLOv8: {str(e)}")
            logger.info("   System will work without it using fallback detection")
    
    def verify_setup(self):
        """Verify models and dependencies"""
        logger.info("\n🔍 Verifying setup...")
        
        # Check for GPU support
        try:
            import torch
            if torch.cuda.is_available():
                logger.info(f"   🚀 GPU detected: {torch.cuda.get_device_name(0)}")
                logger.info(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            else:
                logger.warning("   ⚠️  No GPU detected - will use CPU (slower)")
        except ImportError:
            logger.warning("   ⚠️  PyTorch not installed - ML features unavailable")
            logger.info("   To install: pip install torch torchvision")
        
        # Check core dependencies
        deps_status = []
        deps = [
            ('cv2', 'opencv-python', True),
            ('numpy', 'numpy', True),
            ('torch', 'torch', False),
            ('ultralytics', 'ultralytics', False),
        ]
        
        for module, package, required in deps:
            try:
                __import__(module)
                status = "✅"
            except ImportError:
                status = "❌" if required else "⚠️"
            
            deps_status.append((package, status, required))
            logger.info(f"   {status} {package}")
        
        # Summary
        all_required = all(status == "✅" for _, status, req in deps_status if req)
        if all_required:
            logger.info("\n   ✅ All required dependencies installed!")
            logger.info("   Optional ML dependencies can enhance detection accuracy")
        else:
            logger.warning("\n   ⚠️  Some required dependencies missing")
            logger.info("   Run: pip install -r requirements.txt")

if __name__ == "__main__":
    setup = ModelSetup()
    setup.setup_all()
