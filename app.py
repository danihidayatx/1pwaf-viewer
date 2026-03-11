import sqlite3
import os
import glob
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Gunakan path produksi 1Panel jika ada, fallback ke folder 'data' lokal
PROD_DATA_DIR = '/opt/1panel/apps/openresty/openresty/1pwaf/data'
LOCAL_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

if os.environ.get('WAF_DATA_DIR'):
    DATA_DIR = os.environ.get('WAF_DATA_DIR')
elif os.path.exists(PROD_DATA_DIR):
    DATA_DIR = PROD_DATA_DIR
else:
    DATA_DIR = LOCAL_DATA_DIR

DB_DIR = os.path.join(DATA_DIR, 'db')

print(f"[*] Menggunakan Database Directory: {DB_DIR}")

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    # Simple dashboard stats
    stats = {}
    try:
        conn = get_db_connection(os.path.join(DB_DIR, 'req_log.db'))
        stats['total_attacks'] = conn.execute("SELECT COUNT(*) as count FROM req_logs WHERE is_attack=1").fetchone()['count']
        stats['total_blocks'] = conn.execute("SELECT COUNT(*) as count FROM req_logs WHERE is_block=1").fetchone()['count']
        stats['total_req_logs'] = conn.execute("SELECT COUNT(*) as count FROM req_logs").fetchone()['count']
        conn.close()
    except Exception as e:
        print(f"Error reading req_log.db: {e}")

    try:
        conn = get_db_connection(os.path.join(DB_DIR, '1pwaf.db'))
        waf_stat = conn.execute("SELECT sum(req_count) as req, sum(attack_count) as attacks, sum(count4xx) as c4xx, sum(count5xx) as c5xx FROM waf_stat").fetchone()
        stats['waf_total_req'] = waf_stat['req'] or 0
        stats['waf_total_attacks'] = waf_stat['attacks'] or 0
        conn.close()
    except Exception as e:
         print(f"Error reading 1pwaf.db: {e}")

    return render_template('index.html', stats=stats)


@app.route('/waf-logs')
def waf_logs():
    sites = []
    try:
        conn = get_db_connection(os.path.join(DB_DIR, 'req_log.db'))
        rows = conn.execute("SELECT DISTINCT server_name FROM req_logs WHERE server_name IS NOT NULL AND server_name != '_' AND server_name != '127.0.0.1' ORDER BY server_name").fetchall()
        sites = [row['server_name'] for row in rows]
        conn.close()
    except Exception as e:
        print(f"Error reading sites from req_log.db: {e}")
    return render_template('waf_logs.html', sites=sites)


@app.route('/api/waf-logs')
def api_waf_logs():
    try:
        # DataTables parameters
        draw = request.args.get('draw', type=int)
        start = request.args.get('start', type=int, default=0)
        length = request.args.get('length', type=int, default=10)
        search_value = request.args.get('search[value]', type=str, default='')
        server_name_filter = request.args.get('server_name', type=str, default='')

        conn = get_db_connection(os.path.join(DB_DIR, 'req_log.db'))
        
        query_base = "FROM req_logs "
        query_conditions = []
        params = []
        
        if server_name_filter:
            query_conditions.append("server_name = ?")
            params.append(server_name_filter)
        
        if search_value:
            search_term = f"%{search_value}%"
            query_conditions.append("(ip LIKE ? OR server_name LIKE ? OR uri LIKE ? OR match_rule LIKE ? OR user_agent LIKE ? OR exec_rule LIKE ?)")
            params.extend([search_term]*6)
            
        where_clause = ""
        if query_conditions:
            where_clause = "WHERE " + " AND ".join(query_conditions)
            
        # Total count
        total_records = conn.execute("SELECT COUNT(*) as count FROM req_logs").fetchone()['count']
        
        # Filtered count
        filtered_records = conn.execute(f"SELECT COUNT(*) as count {query_base} {where_clause}", params).fetchone()['count']
        
        # Order by localtime DESC by default
        order_column_index = request.args.get('order[0][column]', type=int, default=0)
        order_dir = request.args.get('order[0][dir]', type=str, default='desc')
        columns = ['localtime', 'ip', 'server_name', 'method', 'uri', 'is_attack', 'is_block', 'match_rule', 'action']
        
        if order_dir not in ['asc', 'desc']:
            order_dir = 'desc'
        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0
            
        order_by = columns[order_column_index]
        
        # Data
        query = f"SELECT * {query_base} {where_clause} ORDER BY {order_by} {order_dir} LIMIT ? OFFSET ?"
        params.extend([length, start])
        
        logs = conn.execute(query, params).fetchall()
        
        data = []
        for log in logs:
            data.append({
                'localtime': log['localtime'],
                'ip': log['ip'],
                'server_name': log['server_name'],
                'method': log['method'],
                'uri': log['uri'],
                'is_attack': log['is_attack'],
                'is_block': log['is_block'],
                'match_rule': log['match_rule'],
                'exec_rule': log['exec_rule'],
                'user_agent': log['user_agent'],
                'action': log['action']
            })
            
        conn.close()
        
        return jsonify({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/site-logs')
def site_logs():
    # Find available sites
    sites = []
    # Check in data/db/sites (old logic) or data/sites
    sites_dir = os.path.join(DB_DIR, 'sites')
    if not os.path.exists(sites_dir):
        sites_dir = os.path.join(DATA_DIR, 'sites')

    if os.path.exists(sites_dir):
        for d in os.listdir(sites_dir):
            # site_req_logs.db is in data/db/sites/domain.com/site_req_logs.db
            db_path = os.path.join(DB_DIR, 'sites', d, 'site_req_logs.db')
            if os.path.isdir(os.path.join(sites_dir, d)) and os.path.exists(db_path):
                sites.append(d)
    
    return render_template('site_logs.html', sites=sites)


@app.route('/api/site-logs/<site_name>')
def api_site_logs(site_name):
    try:
        db_path = os.path.join(DB_DIR, 'sites', site_name, 'site_req_logs.db')
        if not os.path.exists(db_path):
            return jsonify({'error': 'Site database not found.'}), 404

        # DataTables parameters
        draw = request.args.get('draw', type=int)
        start = request.args.get('start', type=int, default=0)
        length = request.args.get('length', type=int, default=10)
        search_value = request.args.get('search[value]', type=str, default='')

        conn = get_db_connection(db_path)
        
        query_base = "FROM site_req_logs "
        query_conditions = []
        params = []
        
        if search_value:
            search_term = f"%{search_value}%"
            query_conditions.append("(ip LIKE ? OR uri LIKE ? OR user_agent LIKE ? OR method LIKE ? OR status_code LIKE ?)")
            params.extend([search_term]*5)
            
        where_clause = ""
        if query_conditions:
            where_clause = "WHERE " + " AND ".join(query_conditions)
            
        # Total count
        total_records = conn.execute("SELECT COUNT(*) as count FROM site_req_logs").fetchone()['count']
        
        # Filtered count
        filtered_records = conn.execute(f"SELECT COUNT(*) as count {query_base} {where_clause}", params).fetchone()['count']
        
        # Order by localtime DESC by default
        order_column_index = request.args.get('order[0][column]', type=int, default=0)
        order_dir = request.args.get('order[0][dir]', type=str, default='desc')
        columns = ['localtime', 'ip', 'method', 'uri', 'status_code', 'request_time', 'browser', 'os']
        
        if order_dir not in ['asc', 'desc']:
            order_dir = 'desc'
        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0
            
        order_by = columns[order_column_index]
        
        # Data
        query = f"SELECT * {query_base} {where_clause} ORDER BY {order_by} {order_dir} LIMIT ? OFFSET ?"
        params.extend([length, start])
        
        logs = conn.execute(query, params).fetchall()
        
        data = []
        for log in logs:
            data.append({
                'localtime': log['localtime'],
                'ip': log['ip'],
                'method': log['method'],
                'uri': log['uri'],
                'status_code': log['status_code'],
                'request_time': log['request_time'],
                'browser': log['browser'],
                'os': log['os']
            })
            
        conn.close()
        
        return jsonify({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
