import os
from flask import Flask, redirect, url_for, request, jsonify, render_template
import socket
import random
import os
import subprocess

app = Flask(__name__)

color = random.choice(["#F0F8FF","#FAEBD7","#F5F5DC","#5F9EA0","#6495ED","#8FBC8F","#E9967A","#FF1493","#FFF0F5","#48D1CC","#4682B4","#D8BFD8"])

def delete_files_in_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

@app.route("/")
def main():
    return render_template('index.html', name=socket.gethostname(), color=color)

@app.route('/fio')
def fio():
    size = request.args.get('size')
    numjobs = request.args.get('numjobs')
    
    rw = request.args.get('rw')
    blocksize = request.args.get('blocksize')
    ioengine = request.args.get('ioengine')
    directory = request.args.get('directory')
    runtime = request.args.get('runtime')
    
    conteinername= socket.gethostname()
    
    fio_command = f"fio --name={conteinername}-{size}-{numjobs} --rw={rw} --blocksize={blocksize} --ioengine={ioengine} --directory={directory} --size={size} --numjobs={numjobs} --runtime={runtime}"
    result = subprocess.run(fio_command.split(), capture_output=True, text=True)

    if result.returncode == 0:
        fio_output = result.stdout
    else:
        fio_output = f"Error running fio: {result.stderr}"

    return render_template('fio.html', name=socket.gethostname(), fio_output=fio_output, fio_command=fio_command)

@app.route('/fiojson')
def fiojson():
    size = request.args.get('size')
    numjobs = request.args.get('numjobs')
    
    rw = request.args.get('rw')
    blocksize = request.args.get('blocksize')
    ioengine = request.args.get('ioengine')
    directory = request.args.get('directory')
    runtime = request.args.get('runtime')
    
    conteinername= socket.gethostname()
    
    fio_command = f"fio --name={conteinername}-{size}-{numjobs} --rw={rw} --blocksize={blocksize} --ioengine={ioengine} --directory={directory} --size={size} --numjobs={numjobs} --runtime={runtime} --output-format=json"
    result = subprocess.run(fio_command.split(), capture_output=True, text=True)

    if result.returncode == 0:
        fio_output = result.stdout
    else:
        fio_output = f"Error running fio: {result.stderr}"

    data = fio_output
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response
    
@app.route("/cleanfiles")
def cleanfiles():
    directory = request.args.get('directory')
    
    delete_files_in_directory(directory)

    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8080")
