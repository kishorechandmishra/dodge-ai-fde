"""
Flask API Server
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from graph_engine import GraphEngine
from query_processor import QueryProcessor

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Global instances
graph_engine = None
query_processor = None


def initialize():
    """Initialize graph and processor"""
    global graph_engine, query_processor
    
    print("Initializing Dodge AI FDE System...")
    
    # Build graph
    graph_engine = GraphEngine('data')
    graph_engine.build_graph()
    
    # Create query processor
    query_processor = QueryProcessor(graph_engine)
    
    print("✅ System ready!")


@app.route('/')
def home():
    """Serve main UI"""
    return send_from_directory('static', 'index.html')


@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'Dodge AI FDE'})


@app.route('/api/graph/summary')
def graph_summary():
    """Get graph statistics"""
    try:
        summary = graph_engine.get_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph/data')
def graph_data():
    """Get graph data for visualization"""
    try:
        max_nodes = request.args.get('max_nodes', 500, type=int)
        data = graph_engine.export_for_viz(max_nodes)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query"""
    try:
        data = request.json
        query_text = data.get('query', '').strip()
        
        if not query_text:
            return jsonify({'error': 'Query required'}), 400
        
        result = query_processor.process(query_text)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    initialize()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
