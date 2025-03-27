Use the following command to generate protobuf files

```bash
protoc --proto_path=./proto --python_out=./proto proto/messages.proto
```

Must use pip install protobuf=3.20

To run, use 
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Requirements

* Install PostgreSQL
```bash
sudo apt update
sudo apt install postgresql-client
```

* Download and run the TimescaleDB Docker image and container
```bash
docker pull timescale/timescaledb-ha:pg17
docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password timescale/timescaledb-ha:pg17
```

* Connect to a db on the PostgreSQL instance
```bash
psql -d "postgres://postgres:password@localhost/postgres"
```