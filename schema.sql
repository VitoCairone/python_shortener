create table if not exists urls (
  id integer primary key autoincrement,
  long_url text not null,
  short_url varchar not null
);