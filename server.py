from flask import Flask, request, jsonify, send_from_directory
from game import Game

app = Flask(__name__, static_folder='static')
game = Game()

MOVES = {
    'up': (0, -1),
    'down': (0, 1),
    'left': (-1, 0),
    'right': (1, 0),
}


def player_id_for(req):
    forwarded = req.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return req.remote_addr


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/register', methods=['POST'])
def register():
    pid = player_id_for(request)
    player = game.register(pid)
    if player is None:
        return jsonify({'error': 'game is full'}), 409
    return jsonify({'player_id': pid, 'color': player['color']})


@app.route('/api/state')
def state():
    game.reap_stale()
    game.touch(player_id_for(request))
    return jsonify(game.state())


@app.route('/api/move', methods=['POST'])
def move():
    data = request.get_json(silent=True) or {}
    direction = data.get('dir')
    if direction not in MOVES:
        return jsonify({'ok': False}), 400
    pid = player_id_for(request)
    game.reap_stale()
    ok = game.move(pid, *MOVES[direction])
    return jsonify({'ok': ok})


@app.route('/api/reset', methods=['POST'])
def reset():
    game.reset()
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)
