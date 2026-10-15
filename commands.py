import subprocess

def run(args:list[str], timeout:int=20) -> subprocess.CompletedProcess:
    try: return subprocess.run(args,text=True,capture_output=True,timeout=timeout,check=False)
    except FileNotFoundError as exc: raise RuntimeError(f"Required command not found: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc: raise RuntimeError(f"Command timed out: {' '.join(args)}") from exc
