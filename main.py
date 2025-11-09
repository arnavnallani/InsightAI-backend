"""
Main Flask application for CourtIQ
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime
import json

from config import Config
from models import Match, MatchConfig, AnalysisResults
from analysis import (
    VideoProcessor, ShotDNA, CounterfactualAnalyzer, 
    MomentumAnalyzer, ShadowAI, FatigueAnalyzer, 
    DecisionHeatmap, ChaosAnalyzer, MatchScorer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Store matches in memory (in production, use database)
matches = {}
analysis_results = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Tennis Coach - Python Backend',
        'version': '2.0',
        'features': [
            'Smart match detection',
            'Enhanced ball tracking',
            'Video validation',
            'Gameplay frame extraction'
        ]
    })

@app.route('/upload')
def upload_page():
    """Upload page"""
    return render_template('upload.html')

@app.route('/upload-video', methods=['POST'])
def upload_video():
    """Handle video upload"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if not file.filename or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload MP4, MOV, AVI, MKV, or WEBM'}), 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    
    file.save(filepath)
    
    match_id = timestamp
    match = Match(
        match_id=match_id,
        upload_date=datetime.now(),
        video_path=filepath,
        processing_status='uploaded'
    )
    
    matches[match_id] = match
    
    from analysis import VideoProcessor
    processor = VideoProcessor(filepath, match)
    first_frame = processor.get_first_frame()
    
    if first_frame is not None:
        import cv2
        frame_path = os.path.join(Config.UPLOAD_FOLDER, f"{match_id}_frame.jpg")
        cv2.imwrite(frame_path, first_frame)
    
    logger.info(f"Video uploaded: {match_id}")
    
    return redirect(url_for('configure', match_id=match_id))

@app.route('/api/extract-gameplay-frame', methods=['POST'])
def extract_gameplay_frame():
    """
    Extract first frame of actual match play (skips intros)
    Used for calibration in frontend
    """
    try:
        logger.info(f"Extract gameplay frame request received")
        logger.info(f"Files in request: {list(request.files.keys())}")
        logger.info(f"Form data in request: {list(request.form.keys())}")
        
        if 'video' not in request.files:
            logger.error("No 'video' field in request.files")
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if not file.filename or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save video temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"temp_{timestamp}_{filename}"
        temp_filepath = os.path.join(Config.UPLOAD_FOLDER, temp_filename)
        file.save(temp_filepath)
        
        try:
            # Create temporary match object for video processing
            from models import Match
            temp_match = Match(
                match_id=f"temp_{timestamp}",
                upload_date=datetime.now(),
                video_path=temp_filepath,
                processing_status='extracting_frame'
            )
            
            # Extract gameplay frame
            from analysis import VideoProcessor
            processor = VideoProcessor(temp_filepath, temp_match)
            gameplay_frame = processor.get_gameplay_frame()
            
            if gameplay_frame is None:
                return jsonify({'error': 'Could not extract gameplay frame'}), 500
            
            # Convert frame to JPEG and encode as base64
            import cv2
            import base64
            _, buffer = cv2.imencode('.jpg', gameplay_frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Clean up temporary file
            try:
                os.remove(temp_filepath)
            except:
                pass
            
            logger.info(f"Successfully extracted gameplay frame from {filename}")
            
            return jsonify({
                'success': True,
                'frame': f'data:image/jpeg;base64,{frame_base64}',
                'message': 'Gameplay frame extracted successfully'
            })
            
        except Exception as e:
            # Clean up on error
            try:
                os.remove(temp_filepath)
            except:
                pass
            raise e
            
    except Exception as e:
        logger.error(f"Error extracting gameplay frame: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-with-calibration', methods=['POST'])
def upload_with_calibration():
    """Handle video upload with court calibration from React frontend"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if not file.filename or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get calibration data
        calibration_str = request.form.get('calibration')
        if not calibration_str:
            return jsonify({'error': 'Missing calibration data'}), 400
        
        calibration = json.loads(calibration_str)
        
        # Validate calibration
        if not calibration.get('corners') or len(calibration['corners']) != 4:
            return jsonify({'error': 'Invalid calibration - need 4 court corners'}), 400
        
        # Save video file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # Create match with calibration
        match_id = timestamp
        match_config = MatchConfig(
            player_position=calibration.get('playerPosition', 'near'),
            num_sets=calibration.get('numSets', 3),
            player_name=calibration.get('playerName', 'Player 1'),
            opponent_name=calibration.get('opponentName', 'Player 2'),
            court_corners=calibration['corners']
        )
        
        match = Match(
            match_id=match_id,
            upload_date=datetime.now(),
            video_path=filepath,
            config=match_config,
            processing_status='calibrated'
        )
        
        matches[match_id] = match
        
        logger.info(f"Video uploaded with calibration: {match_id}")
        logger.info(f"Player: {match_config.player_name} vs {match_config.opponent_name}")
        logger.info(f"Sets: {match_config.num_sets}, Position: {match_config.player_position}")
        
        # Start background processing
        import threading
        thread = threading.Thread(target=process_match_async, args=(match_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'match_id': match_id,
            'status': 'processing',
            'message': 'Video uploaded successfully - AI analysis started'
        })
        
    except Exception as e:
        logger.error(f"Error uploading with calibration: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_match_async(match_id):
    """Process match in background thread"""
    try:
        match = matches.get(match_id)
        if not match:
            logger.error(f"Match {match_id} not found for processing")
            return
        
        match.processing_status = 'processing'
        match.progress = 10
        match.current_stage = 'Initializing video analysis'
        
        # Initialize video processor
        processor = VideoProcessor(match.video_path, match)
        
        # Stage 1: Court calibration (20%)
        match.current_stage = 'Calibrating court dimensions'
        match.progress = 20
        processor.calibrate_court(match.config.court_corners)
        
        # Stage 2: Ball detection and tracking (30%)
        match.current_stage = 'Detecting tennis ball in frames'
        match.progress = 30
        processor.detect_balls()
        
        # Stage 3: Shot analysis (50%)
        match.current_stage = 'Analyzing shot patterns'
        match.progress = 50
        shot_dna = ShotDNA(match)
        shot_dna_data = shot_dna.analyze()
        
        # Stage 4: Counterfactual analysis (60%)
        match.current_stage = 'Computing counterfactual scenarios'
        match.progress = 60
        counterfactual = CounterfactualAnalyzer(match)
        counterfactual_data = counterfactual.analyze()
        
        # Stage 5: Momentum analysis (70%)
        match.current_stage = 'Mapping momentum shifts'
        match.progress = 70
        momentum = MomentumAnalyzer(match)
        momentum_data = momentum.analyze()
        
        # Stage 6: Shadow AI (80%)
        match.current_stage = 'Training your AI clone'
        match.progress = 80
        shadow = ShadowAI(match)
        shadow_data = shadow.analyze()
        
        # Stage 7: Fatigue analysis (85%)
        match.current_stage = 'Identifying fatigue patterns'
        match.progress = 85
        fatigue = FatigueAnalyzer(match)
        fatigue_data = fatigue.analyze()
        
        # Stage 8: Decision heatmap (90%)
        match.current_stage = 'Generating decision heatmap'
        match.progress = 90
        heatmap = DecisionHeatmap(match)
        heatmap_data = heatmap.analyze()
        
        # Stage 9: Chaos theory (95%)
        match.current_stage = 'Detecting butterfly moments'
        match.progress = 95
        chaos = ChaosAnalyzer(match)
        chaos_data = chaos.analyze()
        
        # Stage 10: Finalize (100%)
        match.current_stage = 'Finalizing analysis'
        match.progress = 100
        
        # Compile results
        results = AnalysisResults(
            match_id=match_id,
            shot_dna=shot_dna_data,
            counterfactual=counterfactual_data,
            momentum=momentum_data,
            shadow_self=shadow_data,
            fatigue=fatigue_data,
            decision_heatmap=heatmap_data,
            chaos_theory=chaos_data
        )
        
        analysis_results[match_id] = results
        match.processing_status = 'completed'
        
        logger.info(f"Match {match_id} processing completed")
        
    except Exception as e:
        logger.error(f"Error processing match {match_id}: {str(e)}")
        match = matches.get(match_id)
        if match:
            match.processing_status = 'error'
            match.current_stage = f'Error: {str(e)}'

@app.route('/configure/<match_id>')
def configure(match_id):
    """Configure match settings"""
    match = matches.get(match_id)
    
    if not match:
        return "Match not found", 404
    
    return render_template('configure.html', 
                          match_id=match_id,
                          default_config=Config.DEFAULT_SCORING)

@app.route('/save-config/<match_id>', methods=['POST'])
def save_config(match_id):
    """Save match configuration"""
    match = matches.get(match_id)
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    config_data = request.json
    if not config_data:
        return jsonify({'error': 'No configuration data provided'}), 400
    
    match.user_player = int(config_data.get('user_player', 1))
    match.opponent_player = 2 if match.user_player == 1 else 1
    
    user_name = config_data.get('user_name', 'You')
    opponent_name = config_data.get('opponent_name', 'Opponent')
    match.player_names[match.user_player] = user_name
    match.player_names[match.opponent_player] = opponent_name
    
    match.config = MatchConfig(
        set_format=config_data.get('set_format', 'best_of_3'),
        games_per_set=int(config_data.get('games_per_set', 6)),
        tiebreak_at=int(config_data.get('tiebreak_at', 6)),
        tiebreak_points=int(config_data.get('tiebreak_points', 7)),
        deciding_set_format=config_data.get('deciding_set_format', 'match_tiebreak'),
        match_tiebreak_points=int(config_data.get('match_tiebreak_points', 10)),
        use_ads=config_data.get('use_ads', True),
        use_no_ad=config_data.get('use_no_ad', False)
    )
    
    logger.info(f"Match configuration saved: {match_id}")
    logger.info(f"User is player {match.user_player} ({user_name})")
    logger.info(f"Opponent is player {match.opponent_player} ({opponent_name})")
    
    return jsonify({'success': True, 'next_step': 'calibration'})

@app.route('/calibrate/<match_id>')
def calibrate(match_id):
    """Court calibration page"""
    match = matches.get(match_id)
    
    if not match:
        return "Match not found", 404
    
    processor = VideoProcessor(match.video_path, match)
    first_frame = processor.get_first_frame()
    
    if first_frame is None:
        return "Failed to read video", 500
    
    import cv2
    frame_path = os.path.join(Config.UPLOAD_FOLDER, f"{match_id}_frame.jpg")
    cv2.imwrite(frame_path, first_frame)
    
    return render_template('calibrate.html', 
                          match_id=match_id,
                          match=match,
                          frame_url=url_for('static', filename=f'../uploads/{match_id}_frame.jpg'))

@app.route('/save-calibration/<match_id>', methods=['POST'])
def save_calibration(match_id):
    """Save court calibration and start processing"""
    match = matches.get(match_id)
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    data = request.json
    if not data:
        return jsonify({'error': 'No calibration data provided'}), 400
    
    corners = [
        tuple(data['top_left']),
        tuple(data['top_right']),
        tuple(data['bottom_left']),
        tuple(data['bottom_right'])
    ]
    
    processor = VideoProcessor(match.video_path, match)
    success = processor.calibrate_court(corners)
    
    if not success:
        return jsonify({'error': 'Calibration failed'}), 500
    
    logger.info(f"Court calibrated: {match_id}")
    
    return jsonify({'success': True, 'next_step': 'processing'})

@app.route('/api/status/<match_id>', methods=['GET'])
def api_status(match_id):
    """API endpoint to check processing status (for React frontend)"""
    match = matches.get(match_id)
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    response = {
        'match_id': match_id,
        'status': match.processing_status,
        'progress': getattr(match, 'progress', 0),
        'current_stage': getattr(match, 'current_stage', 'Initializing')
    }
    
    # If completed, include analysis results
    if match.processing_status == 'completed' and match_id in analysis_results:
        results = analysis_results[match_id]
        response['analysis'] = results.to_dict()
    
    return jsonify(response)

@app.route('/processing/<match_id>')
def processing_status(match_id):
    """Show processing status page"""
    match = matches.get(match_id)
    
    if not match:
        return "Match not found", 404
    
    return render_template('processing.html', match_id=match_id, match=match)

@app.route('/process/<match_id>')
def process(match_id):
    """Process video and run analysis (can be called via AJAX)"""
    match = matches.get(match_id)
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    if match.processing_status == 'processing':
        return jsonify({'status': 'already_processing'})
    
    match.processing_status = 'processing'
    
    try:
        logger.info(f"Starting video processing: {match_id}")
        logger.info(f"User: {match.get_user_name()} (Player {match.user_player})")
        logger.info(f"Opponent: {match.get_opponent_name()} (Player {match.opponent_player})")
        
        processor = VideoProcessor(match.video_path, match)
        processor.process_video(frame_skip=Config.FRAME_SKIP)
        
        logger.info(f"Video processing complete: {match_id}")
        logger.info(f"Running analysis: {match_id}")
        
        results = AnalysisResults(
            match_id=match_id,
            generated_at=datetime.now()
        )
        
        results.total_shots = len(match.get_all_shots())
        results.total_rallies = len(match.get_all_rallies())
        
        shot_dna = ShotDNA(match)
        results.shot_dna = shot_dna.analyze()
        
        counterfactual = CounterfactualAnalyzer(match)
        results.counterfactual = counterfactual.analyze()
        
        momentum = MomentumAnalyzer(match)
        results.momentum = momentum.analyze()
        
        shadow = ShadowAI(match)
        results.shadow_self = shadow.analyze()
        
        fatigue = FatigueAnalyzer(match)
        results.fatigue = fatigue.analyze()
        
        heatmap = DecisionHeatmap(match)
        results.decision_heatmap = heatmap.analyze()
        
        chaos = ChaosAnalyzer(match)
        results.chaos_theory = chaos.analyze()
        
        analysis_results[match_id] = results
        
        match.processing_status = 'complete'
        
        logger.info(f"Analysis complete: {match_id}")
        
        return jsonify({'status': 'complete'})
        
    except Exception as e:
        logger.error(f"Processing failed: {match_id} - {str(e)}")
        match.processing_status = 'failed'
        return jsonify({'error': str(e)}), 500


@app.route('/results/<match_id>')
def results(match_id):
    """Display analysis results"""
    match = matches.get(match_id)
    results_data = analysis_results.get(match_id)
    
    if not match or not results_data:
        return "Results not found", 404
    
    formatted_results = results_data.format_for_user(match)
    
    return render_template('results.html', 
                          match=match, 
                          results=results_data,
                          results_json=json.dumps(formatted_results))

def format_player_reference(text: str, match: Match) -> str:
    """
    Replace player numbers with user-friendly names
    Example: "Player 1" becomes "You" or the user's name
    """
    user_name = match.get_user_name()
    opponent_name = match.get_opponent_name()
    
    text = text.replace(f'Player {match.user_player}', user_name)
    text = text.replace(f'player {match.user_player}', user_name.lower())
    text = text.replace(f'Player {match.opponent_player}', opponent_name)
    text = text.replace(f'player {match.opponent_player}', opponent_name.lower())
    
    return text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
