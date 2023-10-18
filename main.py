import json
import sqlite3
import quart
import quart_cors
from quart import request

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

# This key can be anything, though you will likely want a randomly generated sequence.
_SERVICE_AUTH_KEY = "REPLACE_ME"
DATABASE = "todos.db"


def init_db():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS todos
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        todo TEXT NOT NULL)''')
        con.commit()


def assert_auth_header(req):
    assert req.headers.get("Authorization") == f"Bearer {_SERVICE_AUTH_KEY}"


@app.post("/todos/<string:username>")
async def add_todo(username):
    assert_auth_header(request)
    request_data = await request.get_json()
    todo = request_data["todo"]

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("INSERT INTO todos (username, todo) VALUES (?, ?)", (username, todo))
        con.commit()

    return quart.Response(response='OK', status=200)


@app.get("/todos/<string:username>")
async def get_todos(username):
    assert_auth_header(request)

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT todo FROM todos WHERE username=?", (username,))
        todos = cur.fetchall()

    todos_list = [item[0] for item in todos]  # Extracting todos from the fetched tuples
    return quart.Response(response=json.dumps(todos_list), status=200)


@app.delete("/todos/<string:username>")
async def delete_todo(username):
    assert_auth_header(request)
    request_data = await request.get_json()
    todo_idx = request_data["todo_idx"]

    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM todos WHERE username=?", (username,))
        ids = cur.fetchall()

        if 0 <= todo_idx < len(ids):
            cur.execute("DELETE FROM todos WHERE id=?", (ids[todo_idx][0],))
            con.commit()

    return quart.Response(response='OK', status=200)


@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")


@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    init_db()  # initialize the database
    app.run(debug=True, host="0.0.0.0", port=5002)


if __name__ == "__main__":
    main()
