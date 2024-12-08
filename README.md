Use the following command to generate protobuf files

```bash
protoc --proto_path=./proto --python_out=./proto proto/messages.proto
```

Must use pip install protobuf=3.20