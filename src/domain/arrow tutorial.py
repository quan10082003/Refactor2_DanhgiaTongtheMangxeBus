import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd

test_path = 'test.arrow'
schema = ['halo', 'world']
arrow_schema = pa.schema([(name, pa.string()) for name in schema])

data = {
            'halo': ['asd', 'qwe'], 
            'world': ['Asd', 'Zxc']
        }
df = pd.DataFrame(data)

with pa.OSFile(test_path, 'wb') as sink:
    with ipc.new_stream(sink, arrow_schema) as writer:
        table = pa.Table.from_pandas(df, schema=arrow_schema)
        writer.write_table(table)
