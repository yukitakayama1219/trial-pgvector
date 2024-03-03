# 概要
PostgreSQLをUbuntu22.04(WSL2)上に構築し、そこに接続してRAGでナレッジ回答するStreamlitアプリのリポジトリ

# 使い方
## 環境構築
- 仮想環境の設定(`poetry install`)とpre-commitの設定(`pre-commit install`)を実行
```
make install
```

- PostgreSQL on Ubuntu(WSL2)のセットアップ
WSL2でUbuntuを構築する方法は割愛
```
# WSLのデフォルトのリポジトリが古いので、最新情報を取得します。
$ sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
$ wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc |  sudo tee /etc/apt/trusted.gpg.d/pgdg.asc &>/dev/null

# aptで用意されているpg_vectorをインストール
# https://github.com/pgvector/pgvector?tab=readme-ov-file#installation-notes
$ sudo apt install postgresql-15 postgresql-15-pgvector

# postgresqlのサービスを再起動して、activeであることを確認
$ systemctl status postgresql
$ systemctl restart postgresql
$ systemctl status postgresql
```

- DB作成

```
# postgresユーザにOSユーザを切り替え
$ sudo -u postgres -i
# DB所有用ユーザ作成
$ createuser -d -U postgres -P user01
Enter password for new role: 
Enter it again: 

$ psql
psql (15.6 (Ubuntu 15.6-1.pgdg22.04+1))
Type "help" for help.
postgres=# alter role postgres with password '{password}';
postgres=# createdb db01 --encoding=UTF-8 --owner=user01
postgres=# \l
                                             List of databases
   Name    |  Owner   | Encoding | Collate |  Ctype  | ICU Locale | Locale Provider |   Access privileges   
-----------+----------+----------+---------+---------+------------+-----------------+-----------------------
 db01      | user01   | UTF8     | C.UTF-8 | C.UTF-8 |            | libc            | 
 postgres  | postgres | UTF8     | C.UTF-8 | C.UTF-8 |            | libc            | 
 template0 | postgres | UTF8     | C.UTF-8 | C.UTF-8 |            | libc            | =c/postgres          +
           |          |          |         |         |            |                 | postgres=CTc/postgres
 template1 | postgres | UTF8     | C.UTF-8 | C.UTF-8 |            | libc            | =c/postgres          +
           |          |          |         |         |            |                 | postgres=CTc/postgres
(4 rows)

```

- pg_vector有効化
```
# db01に接続
postgres=# \c db01
You are now connected to database "db01" as user "postgres".
db01=# SELECT * FROM pg_available_extensions where name like '%vector%';
  name  | default_version | installed_version |                       comment                        
--------+-----------------+-------------------+------------------------------------------------------
 vector | 0.6.0           | 0.6.0             | vector data type and ivfflat and hnsw access methods
(1 row)

db01=# create extension vector;
CREATE EXTENSION
# vectorのextensionが有効化されたことを確認
db01=# \dx
                             List of installed extensions
  Name   | Version |   Schema   |                     Description                      
---------+---------+------------+------------------------------------------------------
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
 vector  | 0.6.0   | public     | vector data type and ivfflat and hnsw access methods
(2 rows)

db01=# 
```

- .env作成
```
DB_DRIVER=psycopg2
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db01
DB_USER=postgres
PASSWORD={前の手順で設定した値}
OPENAI_API_KEY={Open AI API Keyの値}
```

## アプリ実行
streamlitのアプリを実行する
```
$ poetry shell
$ streamlit run src/app.py

# アプリ起動によってembeddingが作成され、CSVの行数分追加される
# DB上で追加されたレコードを見る
$ psql -u postgres -h localhost -d db01
Password for user postgres: 
psql (15.6 (Ubuntu 15.6-1.pgdg22.04+1))
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, compression: off)
Type "help" for help.

db01=# \d langchain_pg_embedding
db01=# select collection_id, document, cmetadata, custom_id, uuid from langchain_pg_embedding;
# collection_nameに指定されたembeddingのcollectionも1つ作成される
db01=# \d langchain_pg_collection
db01=# select name, cmetadata, uuid from langchain_pg_collection
``` 