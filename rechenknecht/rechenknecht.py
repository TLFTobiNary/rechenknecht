from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash
from sqlite3 import IntegrityError
from auth import login_required, admin_required
from db import get_db

from os import mkdir, listdir
from os.path import isfile, join, realpath
from base64 import b64encode, b64decode
from decimal import *
bp = Blueprint('rechenknecht', __name__)


class User:
    def __init__(self, userid, name):
        self.name = name
        self.userid = userid
    def __str__(self):
        return self.name
    

class Credit:
    def __init__(self, debitor, creditor):
        if debitor == creditor:
            raise Exception("this shouldn't happen, one can't owe to oneself")
        self.debitor = debitor
        self.creditor = creditor
        self.debit = 0
    def __str__(self):
        return self.debitor.name + " owes "+str(self.debit/100)+" to "+self.creditor.name
    def __eq__(self, other):
        if isinstance(other, Credit):
            return (self.debitor in [other.debitor, other.creditor]) and (self.creditor in [other.debitor, other.creditor])
        else:
            return False

    def addDebt(self, debitor, creditor, amount):
        if debitor in [self.debitor, self.creditor] and creditor in [self.debitor, self.creditor]:
            if debitor == self.debitor:
                self.debit += amount
            else:
                self.debit -=  amount
        
            d = self.debitor
            c = self.creditor
            if self.debit < 0:
                self.creditor = d
                self.debitor = c
                self.debit = self.debit * (-1)

        else:
            raise Exception("trying to add debt to a user not involved in this relationship")
                
class CreditList:
    def __init__(self):
        self.credits = []
    def getOrCreate(self, user1, user2):
        c = Credit(user1, user2)
        for x in self.credits:
            if x == c:
                return x
        self.credits.append(c)
        return c


class Pool:
    def __init__(self, poolid, description):
        self.poolid = poolid
        self.description = description
        self.members = []
        self.purchases = []
    def size(self):
        return len(self.members)
    def addUser(self, user):
        self.members.append(user)
    def addPurchase(self, purchase):
        self.purchases.append(purchase)
    def __str__(self):
        return "Pool "+self.description
    def calculateBalances(self, creditlist):
        balances = {}
        for u in self.members:
            balances[u] = 0

        for p in self.purchases:
            if p.user not in balances.keys():
                balances[p.user] = 0
            balances[p.user] += p.price
            # todo make a better solution that doesn't create or destroy money in tiny amounts
            splitAmount =   p.price/self.size()
            for m in self.members:
               balances[m] -= splitAmount
               if m != p.user:
                   c = creditlist.getOrCreate(m, p.user)
                   c.addDebt(m, p.user, splitAmount)
        return balances


class Purchase:
    def __init__(self, price, user, description):
        self.price = price
        self.user = user
        self.description = description
    def __str__(self):
        return str(self.user) + " bought " + self.description + " for " + str(self.price)


def generateModels():
    db = get_db()
    pools = db.execute("select * from pools").fetchall()
    users = db.execute("select id, username from users").fetchall()
    poolsusers = db.execute("select * from poolsusers").fetchall()
    runspurchases = db.execute("select items.description as description, purchases.price as price, purchases.userid as userid, purchases.poolid as poolid from runs inner join purchases on runs.id = purchases.runid inner join items on items.id = purchases.itemid where runs.paid=False").fetchall()
    userDict = {}
    poolDict = {}
    for u in users:
        userDict[u['id']] = User(u['id'], u['username'])

    for p in pools:
        poolDict[p['id']] = Pool(p['id'], p['description'])

    for p in poolsusers:
        poolDict[p['pool']].addUser(userDict[p['user']])

    for r in runspurchases:
        p = Purchase(r['price'], userDict[r['userid']], r['description'])
        poolDict[r['poolid']].addPurchase(p)

    return(userDict, poolDict)

def calculate_credit_list():
    (userDict, poolDict) = generateModels()
    poolBalances = []
    creditList = CreditList()
    for p in poolDict.values():
        balances = p.calculateBalances(creditList)
        poolBalances.append((p.description, balances.items()))
    return creditList



@bp.route('/')
@login_required
def index():
    db = get_db()

    runs = db.execute("select runs.id as id, runs.date as date, runs.paid as paid, shops.name as shopname from runs inner join shops on runs.shopid = shops.id order by paid, date DESC").fetchall()
    shops = db.execute("select * from shops order by name ASC").fetchall()
    
    
    creditList = calculate_credit_list()

    

    return render_template('rechenknecht/dashboard.html', runs=runs, creditList = creditList, shops=shops)

@bp.route('/run/add', methods=("POST",))
@login_required
def addRun():
    shopid = request.form.get("shopid")
    date = request.form.get("date")

    db = get_db()
    result = db.execute("insert into runs (shopid, date) values(?, ?)", (shopid, date))
    db.commit()
    newRun = result.lastrowid


    return redirect(url_for("rechenknecht.editRun", runid=newRun))


@bp.route('/canihazrunpayment', methods=("POST",))
@admin_required
def markPaid():
    db = get_db()
    runs = request.form.getlist("runs[]")
    for run in runs:
        try:
            int(run)
            db.execute("update runs set paid=True where id = ?", (run,))
        except:
            flash("that wasn't a real run.")
            redirect(url_for("index"))
    db.commit()
    return redirect(url_for("index"))


@bp.route('/run/<int:runid>',methods=("GET", "POST"))
@login_required
def editRun(runid):
    if request.method == 'GET':
        db = get_db()
        purchases = db.execute("select purchases.id as id, purchases.price as price, items.description as itemName, pools.description as poolName from purchases inner join items on purchases.itemid = items.id inner join pools on purchases.poolid = pools.id where runid = ?", (runid,)).fetchall()
        run = db.execute("select runs.id as id, runs.shopid as shopid, runs.date as date, runs.paid as paid, shops.name as name from runs inner join shops on runs.shopid=shops.id where runs.id = ?", (runid,)).fetchone()
        items = db.execute("select * from items where shopid = ? ORDER BY price ASC", (run['shopid'],)).fetchall()
        pools = db.execute("select * from pools where disabled = ?",  (False,)).fetchall()
        
        return render_template('rechenknecht/run.html', purchases=purchases, items=items, pools=pools, run=run)

    if request.method == 'POST':
        if request.form.get("modify"):
            session["oldrunid"] = runid
            return redirect(url_for("rechenknecht.editItem", itemid=request.form.get("item")))
        db = get_db()
        qty = request.form.get("qty")
        item = request.form.get("item")
        itemPrice = db.execute("select price from items where id = ?", (item,)).fetchone()['price']
        pool = request.form.get("pool")
        for i in range(int(qty)):
            db.execute("insert into 'purchases' ('runid', 'itemid', 'price', 'userid', 'poolid') values (?, ?, ?, ?, ?)",
                (runid, item, itemPrice, g.user['id'], pool))
        db.commit()
        return redirect(url_for("rechenknecht.editRun", runid=runid))

@bp.route("/purchase/<int:purchaseid>/del", methods=("POST",))
@login_required
def deletePurchase(purchaseid):
    db = get_db()
    p = db.execute("select userid, runid from purchases where id = ?", (purchaseid,)).fetchone()
    if g.user['id'] == p['userid']:
        db.execute("delete from purchases where id = ?", (purchaseid,))
        db.commit()
    else:
        flash("Only the user that bought this can remove this.")
    return redirect(url_for("rechenknecht.editRun", runid=p['runid']))


@bp.route("/item/new", methods=("GET", "POST"))
@bp.route("/item/<int:itemid>", methods=("GET", "POST"))
@login_required
def editItem(itemid = -1):
    #edit an item
    db = get_db()
    if request.method == "GET":
        item = db.execute("select * from items where id = ?", (itemid,)).fetchone()
        if item is None:
            item = {"new": True}
        shops = db.execute("select * from shops").fetchall()
        return render_template('rechenknecht/item.html', item=item, shops=shops)
    else:
        desc = request.form.get("name")
        shop = request.form.get("shop")
        if db.execute("select * from shops where id = ?", (shop,)).fetchone() is None:
            flash("This shop doesn't exist.")
            return redirect(url_for("rechenknecht.editItem",itemid=itemid))
        price = int(Decimal(request.form.get("price"))*100)
        if request.form.get("delete"):
            db.execute("delete from items where id=?", (itemid,))
            db.commit()
            flash("Item has been deleted.")
            if "oldrunid" in session:
                x = session.pop("oldrunid", None)
                return redirect(url_for('rechenknecht.editRun', runid=x))
            else:
                return redirect(url_for('rechenknecht.settings'))
        elif request.form.get("create"):
                newId = db.execute("insert into items (description, shopid, price) values(?,?,?)", (desc, shop, price))
                db.commit()
                return redirect(url_for("rechenknecht.editItem", itemid=newId.lastrowid))
        else:
            db.execute("update items set description=?, shopid=?, price=? where id=?", (desc,shop,price,itemid))
            db.commit()
        if "oldrunid" in session:
            x = session.pop("oldrunid", None)
            return redirect(url_for('rechenknecht.editRun', runid=x))
        return redirect(url_for('rechenknecht.editItem', itemid=itemid))

@bp.route("/settings")
@login_required
def settings():
    db = get_db()
    pools = db.execute("select * from pools").fetchall()
    users = db.execute("select id, username, privileges, disabled from users").fetchall()
    items = db.execute("select * from items inner join shops on items.shopid=shops.id order by description ASC").fetchall()
    shops = db.execute("select * from shops").fetchall()
    return render_template('rechenknecht/settings.html', pools=pools, users=users, items=items, shops=shops)


@bp.route("/user/<int:userid>", methods=("GET", "POST"))
@bp.route("/user/new", methods=("POST", "GET"))
@admin_required
def editUser(userid = -1):
    db = get_db()
    if request.method == "GET":
        user = db.execute("select * from users where id = ?", (userid,)).fetchone()
        if user is None:
            user = {"new": True}
        return render_template("rechenknecht/user.html", user=user)
    else:
        darkmode = False
        if request.form.get("darkmode"):
            darkmode = True
        disabled = False
        if request.form.get("disabled"):
            disabled = True
        username = request.form.get("username")
        privs = request.form.get("privileges")
        password = None
        if len(request.form.get("password")) > 0:
                password = generate_password_hash(request.form.get("password"))

        if userid == -1:
            # this is a new user :)
            if not password:
                flash("new users need passwords.")
                return redirect(url_for("rechenknecht.editUser"))
            newUser = db.execute("insert into users ('username', 'password', 'privileges', 'darkmode', 'disabled') values (?,?,?,?, ?)", (username, password, privs, darkmode, disabled))
            db.commit()
            newUserId = newUser.lastrowid
            newPool = db.execute("insert into pools ('description') values (?)", (username,))
            db.commit()
            newPoolId = newPool.lastrowid

            db.execute("insert into poolsusers ('user', 'pool') values (?, ?)", (newUserId, newPoolId))
            db.commit()
            return redirect(url_for("rechenknecht.editUser", userid=newUserId))
        else:
            if disabled:
                # should this be okay?
                cl = calculate_credit_list()
                for c in cl.credits:
                    if c.creditor.userid == userid or c.debitor.userid == userid:
                        flash("This user has open balances. These must be settled first.")
                        return redirect(url_for("rechenknecht.editUser", userid=userid))
            if password:
                db.execute("update users set password=? where id=?", (password, userid))
            db.execute("update users set username = ?, privileges = ?, disabled = ?, darkmode = ? where id = ?", (username, privs, disabled, darkmode, userid))
            db.commit()
            return redirect(url_for("rechenknecht.editUser", userid=userid))

@bp.route("/pool/new", methods=("POST", "GET"))
@bp.route("/pool/<int:poolid>", methods=("POST", "GET"))
@admin_required
def editPool(poolid = -1):
    if request.method == "GET":
        db = get_db()
        pool = db.execute("select * from pools where id = ?", (poolid,)).fetchone()
        if not pool:
            pool = {"new":True}
        users = db.execute("select * from users where disabled=?", (False,)).fetchall()
        poolsusers = db.execute("select * from poolsusers where pool=?", (poolid,)).fetchall()
        mem = []
        for x in poolsusers:
            mem.append(x['user'])

        return render_template("rechenknecht/pool.html", pool=pool, users=users, members=mem)
    else:
        db = get_db()
        if poolid == -1:
            desc = request.form.get("name")
            mem = request.form.getlist("members")
            newPool = db.execute("insert into pools ('description') values (?)", (desc,))
            db.commit()
            newPoolId = newPool.lastrowid

            for x in mem:
                activeUser = db.execute("select * from users where id=? and disabled=?",(x, False)).fetchone()
                if activeUser:
                    db.execute("insert into poolsusers ('user', 'pool') values (?, ?)", (x, newPoolId))
                else:
                    flash("You asked me to add a deactivated user to a pool. Not gonna happen.")
            db.commit()
            return redirect(url_for("rechenknecht.editPool", poolid=newPoolId))

        if request.form.get("enable"):
            db.execute("update pools set disabled=? where id=?", (False, poolid))
            db.commit()
            flash("pool has been enabled.")
            return redirect(url_for("rechenknecht.editPool", poolid=poolid))
        openRun = db.execute("select * from runs inner join purchases on runs.id = purchases.runid where runs.paid = ? and purchases.poolid = ?", (False, poolid)).fetchone()
        if request.form.get("deactivate"):
            if openRun:
                flash("This pool has open balanches and cannot be disabled.")
                return redirect(url_for("rechenknecht.editPool", poolid=poolid))
            else:
                db.execute("update pools set disabled=? where id=?", (True, poolid))
                db.commit()
                flash("pool has been disabled.")
                return redirect(url_for("rechenknecht.editPool", poolid=poolid))

        desc = request.form.get("name")
        mem = request.form.getlist("members")
        db.execute("update pools set description=? where id = ?", (desc, poolid))

        # has this pool open balances?
        if openRun:
            db.commit()
            flash("This pool has unpaid balances and members cannot be modified.")
            return redirect(url_for("rechenknecht.editPool", poolid=poolid))

        db.execute("delete from poolsusers where pool = ?", (poolid,))
        for x in mem:
            activeUser = db.execute("select * from users where id=? and disabled=?",(x, False)).fetchone()
            if activeUser:
                db.execute("insert into poolsusers ('user', 'pool') values (?, ?)", (x, poolid))
            else:
                flash("You asked me to add a deactivated user to a pool. Not gonna happen.")
        db.commit()
        return redirect(url_for('rechenknecht.editPool', poolid=poolid))


@bp.route("/shop/add", methods=("POST",))
@login_required
def addShop():
    db = get_db()
    try:
        cursor = db.execute("insert into shops ('name') values (?)", ("New Shop",))
        db.commit()
        newShopId = cursor.lastrowid
        return redirect(url_for("rechenknecht.editShop", shopid=newShopId))
    except IntegrityError:
        flash("You need to edit the shop with this name first")
        return redirect(url_for("rechenknecht.settings"))

@bp.route("/shop/new", methods=("POST", "GET"))
@bp.route("/shop/<int:shopid>", methods=("POST", "GET"))
@login_required
def editShop(shopid = -1):
    if request.method == "GET":
        db = get_db()
        shop = db.execute("select * from shops where id = ?", (shopid,)).fetchone()
        if not shop:
            shop = {"new": True}
        return render_template("rechenknecht/shop.html", shop=shop)
    else:
        # get the form data and edit the shop, i guess?
        db = get_db()
        name = request.form.get("name")
        if shopid == -1:
           newShop = db.execute("insert into shops ('name') values(?)",(name,))
           db.commit()
           return redirect(url_for("rechenknecht.editShop", shopid=newShop.lastrowid))
        else:
            if request.form.get("delete"):
                item = db.execute("select * from items where shopid=?",(shopid,)).fetchone()
                if item:
                    flash("Shop still has items. You can't delete shops with items.")
                    return redirect(url_for("rechenknecht.editShop", shopid=shopid))
                else:    
                    db.execute("delete from shops where id = ?",(shopid,))
                    db.commit()
                    flash("Shop has been deleted.")
                    return redirect(url_for("rechenknecht.settings"))
            else:
                db.execute("update shops set name=? where id = ?", (name, shopid))
                db.commit()
                return redirect(url_for("rechenknecht.editShop", shopid=shopid))


@bp.route("/canihazdarkmode", methods=("POST",))
@login_required
def toggleMode():
    db = get_db()
    newVal = not g.user['darkmode']
    db.execute("update users set darkmode = ? where id = ?", (newVal, g.user['id']))
    db.commit()
    return redirect(url_for("rechenknecht.settings"))

