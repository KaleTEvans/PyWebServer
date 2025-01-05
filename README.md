Use the following command to generate protobuf files

```bash
protoc --proto_path=./proto --python_out=./proto proto/messages.proto
```

Must use pip install protobuf=3.20

To run, use 
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```