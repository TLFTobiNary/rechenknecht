# Rechenknecht
Rechenknecht is supposed to be a simple low-ressource web application/tool to track expenses over groups of people.
The idea is to create pools of people and people can add expenses to the pool. Rechenknecht will calculate the debts that need to be settled to even out the expenses of the different pool members.

# Known issues

- under special circumstances, debts might be off by a few cents.
- No internationalization.
- Shops can't be deleted (should be easy, tho.)
- Pools can't be deleted (should be non-trivial; debts may be pending.)
- settings show all available settings, regardless of the privs.
- privs are wonky.
- statistics are not available.
- optional switch from sqlite to postgres would be nice.


# quick start
On an `apt`-distro, run:
```
sudo apt install python3-flask uwsgi uwsgi-plugin-python3
./run.sh
```

The application should be available on <a href="http://localhost:8080">localhost:8080</a>. The user "admin" has password "admin" and is admin. The database will be created in "rechenknecht/instance/sqlite.db".

For production use, please consider using a reverse proxy in front of `uwsgi` to add TLS and resiliency.
