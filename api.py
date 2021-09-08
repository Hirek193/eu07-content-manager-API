from flask import request
import flask, mysql.connector, json, os.path, random, string, config
api = flask.Flask(__name__)
conn = mysql.connector.connect(host=config.host,
                                         database=config.database,
                                         user=config.user,
                                         password=config.password)

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def getDataFromDatabase(query, database):
    database.reconnect(attempts=10)
    cur = database.cursor()
    statistics = cur.execute(query)
    columns = cur.description
    result = []
    for value in cur.fetchall():
        tmp = {}
        for (index, column) in enumerate(value):
            tmp[columns[index][0]] = column
        result.append(tmp)
    return result

def executeCommand(query, database):
    database.reconnect(attempts=10)
    cur = database.cursor()
    cur.execute(query)


@api.errorhandler(500)
def error500(err):
    errJson = {
        'succes': False,
        'message': 'Internal server error. Contact administrator.'
    }
    return json.dumps(errJson), 500

@api.errorhandler(404)
def error500(err):
    errJson = {
        'succes': False,
        'message': 'Resource not found. Check your route.'
    }
    return json.dumps(errJson), 404


@api.route('/v1/getAddons', methods=['GET'])
def get_getAddons():
    return json.dumps(getDataFromDatabase("SELECT * FROM `addons_db` ORDER BY `addons_db`.`id` ASC", conn))

@api.route('/v1/getAddon/<modId>', methods=['GET'])
def get_getAddon(modId):
    sql = str.format("SELECT filename FROM `addons_db` WHERE id={0};", modId)
    cur = conn.cursor()
    cur.execute(sql)
    fetched = cur.fetchall()
    length = len(fetched)
    if (length == 1):
        filename = str(fetched[0][0])
        filename = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/') + "/mods/" + filename
        filename = str(filename)
        if (os.path.isfile(filename) == False):
            trace = id_generator()
            print(trace)
            retJson = {
                'succes': False,
                'message': 'Modification not found',
                'traceCode': trace
            }
            return json.dumps(retJson), 404
        response = flask.send_file(as_attachment=True, path_or_file=filename)
        return response
    elif (length == 0):
        trace = id_generator()
        print(trace)
        retJson = {
            'succes': False,
            'message': 'Modification ID not found',
            'traceCode': trace
        }
        return json.dumps(retJson), 404
    else:
        trace = id_generator()
        print(trace)
        retJson = {
            'succes': False,
            'message':'Mutliple ID\'s found. Contact administrator.',
            'traceCode': trace
        }
        return json.dumps(retJson), 404

@api.route('/v1/addAddon', methods=['POST'])
def POST_addAddon():
    token = request.headers.get("uploader-token")
    type = request.headers.get("Content-Type")
    if (type == "application/octet-stream"):
        sql = str.format("SELECT * FROM `uploader_tokens` WHERE token='{0}';", token)
        cur = conn.cursor()
        cur.execute(sql)
        fetched = cur.fetchall()
        length = len(fetched)
        if (length == 1):
            addAddedBy = fetched[0][1]
            addName = request.args.get("name")
            addDescription = request.args.get("description")
            addAuthor = request.args.get("author")
            addVersion = request.args.get("version")
            addFilename = str.format("{0}-{1}-{2}.zip", addAuthor, addName, addVersion)
            addType = request.args.get("type")

            print(addName)
            if(addAddedBy == None or addName == None or addDescription == None or addAuthor == None or addVersion == None or addType == None or request.data == None):
                trace = id_generator()
                print(trace)
                retJson = {
                    'succes':False,
                    'message':"Not enought parameters.",
                    'traceCode': trace
                }
                return retJson
            else:
                sql = str.format(
                    "INSERT INTO `addons_db` (`id`, `name`, `description`, `author`, `added_by`, `version`, `filename`, `addonType`) VALUES (NULL, '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}');",
                    addName, addDescription, addAuthor, addAddedBy, addVersion, addFilename, addType)

                filename = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/') + "/mods/" + addFilename
                with open(filename, 'wb') as f:
                    f.write(request.data)
                    f.close()
                retJson = {
                    'succes': True,
                    'uuid':token,
                    'username': addAddedBy
                }
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                return retJson, 200
        else:
            trace = id_generator()
            print(trace)
            retJson = {
                'succes': False,
                'message': 'Invalid token provided.',
                'traceCode': trace
            }
            return json.dumps(retJson), 403
    else:
        trace = id_generator()
        print(trace)
        retJson = {
            'succes': False,
            'message':'Unrecognized content-type.',
            'traceCode':trace
        }
        return json.dumps(retJson), 406

#@api.route('/v1/getManager', methods=['GET'])
#def get_getManager():
#    filename = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/') + "/cm/manager.zip"
#    response = flask.send_file(as_attachment=True, path_or_file=filename)
#    return response


api.run(port=90, host="0.0.0.0")