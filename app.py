import os
import shutil
from flask import Flask, redirect, url_for, request, json, jsonify, render_template, send_from_directory
import socket
import random
import subprocess
import time

app = Flask(__name__)

color = random.choice(["#F0F8FF","#FAEBD7","#F5F5DC","#5F9EA0","#6495ED","#8FBC8F","#E9967A","#FF1493","#FFF0F5","#48D1CC","#4682B4","#D8BFD8"])

@app.route('/dog.jpg')
def get_dog_image():
    return send_from_directory(os.path.join(app.root_path, 'templates'), 'dog.jpg')

def delete_files_in_directory(directory):
    if not directory or not os.path.exists(directory):
        return
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def generate_mock_fio_json(size, numjobs, rw, blocksize, ioengine, directory, runtime):
    try:
        numjobs_val = int(numjobs) if numjobs else 1
    except:
        numjobs_val = 1
        
    try:
        runtime_val = float(runtime) if runtime else 60.0
    except:
        runtime_val = 60.0

    # Determine basic throughput (MB/s) and IOPS based on blocksize
    bs_factor = 4096
    if blocksize:
        bs_str = str(blocksize).lower()
        if 'k' in bs_str:
            try: bs_factor = int(bs_str.replace('k', '')) * 1024
            except: pass
        elif 'm' in bs_str:
            try: bs_factor = int(bs_str.replace('m', '')) * 1024 * 1024
            except: pass
        elif 'g' in bs_str:
            try: bs_factor = int(bs_str.replace('g', '')) * 1024 * 1024 * 1024
            except: pass

    base_bw_mb = random.uniform(80.0, 250.0) # baseline drive speed 80-250 MB/s
    if bs_factor < 16384: # 4k or smaller
        base_bw_mb = random.uniform(25.0, 65.0)
    elif bs_factor > 524288: # 512k or larger
        base_bw_mb = random.uniform(350.0, 650.0)

    jobs = []
    for i in range(numjobs_val):
        bw_mb = base_bw_mb * random.uniform(0.92, 1.08)
        bw_kb = bw_mb * 1024.0
        iops = (bw_kb * 1024.0) / bs_factor

        r_bw = 0.0
        r_iops = 0.0
        w_bw = 0.0
        w_iops = 0.0

        rw_str = str(rw).lower() if rw else 'rw'
        if 'read' in rw_str or rw_str == 'read':
            r_bw = bw_kb
            r_iops = iops
        elif 'write' in rw_str or rw_str == 'write':
            w_bw = bw_kb
            w_iops = iops
        else: # mixed rw or randrw
            r_bw = bw_kb * 0.5
            r_iops = iops * 0.5
            w_bw = bw_kb * 0.5
            w_iops = iops * 0.5

        job = {
            "jobname": f"{socket.gethostname()}-{size}-{numjobs}",
            "groupid": 0,
            "error": 0,
            "job options": {
                "name": f"{socket.gethostname()}-{size}-{numjobs}",
                "rw": rw or "rw",
                "blocksize": blocksize or "4k",
                "ioengine": ioengine or "libaio",
                "directory": directory or "/tmp",
                "size": size or "100m",
                "numjobs": str(numjobs),
                "runtime": str(runtime)
            },
            "read": {
                "io_bytes": int(r_bw * 1024.0 * runtime_val),
                "bw": r_bw,
                "iops": r_iops,
                "runtime": int(runtime_val * 1000.0),
                "lat_ns": {
                    "min": random.randint(1200, 3000),
                    "max": random.randint(60000, 400000),
                    "mean": random.uniform(15000, 45000),
                    "stddev": random.uniform(3000, 9000)
                }
            },
            "write": {
                "io_bytes": int(w_bw * 1024.0 * runtime_val),
                "bw": w_bw,
                "iops": w_iops,
                "runtime": int(runtime_val * 1000.0),
                "lat_ns": {
                    "min": random.randint(1200, 3000),
                    "max": random.randint(60000, 400000),
                    "mean": random.uniform(15000, 45000),
                    "stddev": random.uniform(3000, 9000)
                }
            }
        }
        jobs.append(job)

    mock_data = {
        "fio version": "fio-3.28-mock",
        "timestamp": int(time.time()),
        "time": time.ctime(),
        "jobs": jobs
    }
    return json.dumps(mock_data)

@app.route("/")
def main():
    return render_template('index.html', name=socket.gethostname(), color=color)

@app.route('/fio')
def fio():
    size = request.args.get('size') or '100m'
    numjobs = request.args.get('numjobs') or '1'
    
    rw = request.args.get('rw') or 'rw'
    blocksize = request.args.get('blocksize') or '4k'
    ioengine = request.args.get('ioengine') or 'libaio'
    directory = request.args.get('directory') or '/tmp'
    runtime = request.args.get('runtime') or '30'
    
    conteinername = socket.gethostname()
    
    fio_command = f"fio --name={conteinername}-{size}-{numjobs} --rw={rw} --blocksize={blocksize} --ioengine={ioengine} --directory={directory} --size={size} --numjobs={numjobs} --runtime={runtime}"
    
    try:
        result = subprocess.run(fio_command.split(), capture_output=True, text=True)
        if result.returncode == 0:
            fio_output = result.stdout
        else:
            fio_output = f"Error running fio: {result.stderr}"
    except FileNotFoundError:
        # Generate simulated textual FIO output
        jobs_cnt = int(numjobs) if numjobs else 1
        fio_output = (
            f"fio-3.28-mock (Simulated output because 'fio' is not installed)\n"
            f"Starting {jobs_cnt} thread jobs...\n"
            f"rw={rw or 'rw'}, bs={blocksize or '4k'}, ioengine={ioengine or 'libaio'}, dir={directory or '/tmp'}\n"
            f"Running stress test for {runtime or '60'} seconds...\n"
            f"Jobs completed successfully.\n\n"
            f"Run status group 0 (all jobs):\n"
        )
        if 'read' in str(rw).lower() or not rw or 'rw' in str(rw).lower():
            fio_output += f"   READ: bw=48.6MiB/s (51.0MB/s), IOPS={12450}, io={size or '100m'}\n"
        if 'write' in str(rw).lower() or not rw or 'rw' in str(rw).lower():
            fio_output += f"  WRITE: bw=49.1MiB/s (51.5MB/s), IOPS={12570}, io={size or '100m'}\n"
            
    return render_template('fio.html', name=socket.gethostname(), fio_output=fio_output, fio_command=fio_command)

# add fio json
@app.route('/fiojson')
def fiojson():
    size = request.args.get('size') or '100m'
    numjobs = request.args.get('numjobs') or '1'
    
    rw = request.args.get('rw') or 'rw'
    blocksize = request.args.get('blocksize') or '4k'
    ioengine = request.args.get('ioengine') or 'libaio'
    directory = request.args.get('directory') or '/tmp'
    runtime = request.args.get('runtime') or '30'
    
    conteinername = socket.gethostname()
    
    fio_command = f"fio --name={conteinername}-{size}-{numjobs} --rw={rw} --blocksize={blocksize} --ioengine={ioengine} --directory={directory} --size={size} --numjobs={numjobs} --runtime={runtime} --output-format=json"
    
    try:
        result = subprocess.run(fio_command.split(), capture_output=True, text=True)
        if result.returncode == 0:
            fio_output = result.stdout
        else:
            fio_output = f"Error running fio: {result.stderr}"
    except FileNotFoundError:
        # Return simulated JSON
        fio_output = generate_mock_fio_json(size, numjobs, rw, blocksize, ioengine, directory, runtime)

    try:
        json.loads(fio_output)
        data = fio_output
        status_code = 200
    except (ValueError, TypeError):
        data = json.dumps({"error": fio_output})
        status_code = 500

    response = app.response_class(
        response=data,
        status=status_code,
        mimetype='application/json'
    )
    return response

@app.route("/cleanfiles")
def cleanfiles():
    directory = request.args.get('directory') or '/tmp'
    delete_files_in_directory(directory)
    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

