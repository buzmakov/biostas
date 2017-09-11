from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)

def get_mongodb():
    from pymongo import MongoClient

    client = MongoClient('mongodb://doctor:doctorStas@ds133044.mlab.com:33044/biomarker')
    # client = MongoClient('172.17.0.2', 27017)
    db = client['biomarker']
    return db

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/init')
def update_data_from_file():

    markers_collection = get_mongodb().markers_collection

    data_file = os.path.join(os.path.dirname(__file__),'data','Data Model.xlsx')
    xl = pd.ExcelFile(data_file)
    my_markers = xl.parse('Structures #1 & #2')
    res = []

    # Get list of markers
    my_markers = xl.parse('Structures #1 & #2')
    for marker_index in my_markers.index:
        marker = {}
        marker['Type'] = my_markers.at[marker_index, 'Type']
        marker['Category'] = my_markers.at[marker_index, 'Category']
        marker['Subcategory'] = my_markers.at[marker_index, 'Subcategory']
        marker['Instance'] = my_markers.at[marker_index, 'Instance']
        if markers_collection.find(marker).count() == 0:
            res.append('Inserting: {}'.format(marker))
            markers_collection.insert_one(marker)
        else:
            res.append('Skiping: {}'.format(marker))

    # Get markers parameters
    markers_description = xl.parse('Lib2 Biomarkers')
    for marker_index in markers_description.index:
        marker = {}
        marker['Instance'] = markers_description.at[marker_index, 'Biomarker name']
        marker['BiomarkerID'] = markers_description.at[marker_index, 'BiomarkerID']
        marker['Lower Limit'] = markers_description.at[marker_index, 'Lower Limit']
        marker['Upper Limit'] = markers_description.at[marker_index, 'Upper Limit']
        marker['Units'] = markers_description.at[marker_index, 'Units']
        for db_marker in markers_collection.find({'Instance': marker['Instance']}):
            res.append('Update: {}'.format(db_marker))
            markers_collection.find_one_and_update(
                {'_id': db_marker['_id']},
                {'$set': marker}
            )

    # Get intervantion parameters
    #TODO: add it

    # Read markers values
    markers_description = xl.parse('Data Sample')
    for marker_index in markers_description.index:
        if marker_index == 0:
            continue
        marker = {}
        marker['Instance'] = markers_description.iloc[marker_index][7]
        marker['values'] = []
        for i in range(9, markers_description.shape[1]):
            marker['values'].append(
                {
                    'date': markers_description.iloc[0, i],
                    'value': markers_description.iloc[marker_index, i],
                })
        for db_marker in markers_collection.find({'Instance': marker['Instance']}):
            res.append('Update: {}'.format(db_marker))
            markers_collection.find_one_and_update(
                {'_id': db_marker['_id']},
                {'$set': marker}
            )

    return render_template('init.html', items=res)

@app.route('/markers')
def get_markers():
    markers_collection = get_mongodb().markers_collection
    markers = list(markers_collection.find({}))
    # markers = sorted(markers, key=lambda x:x['Instance'])
    return render_template('markers.html', markers = markers)

@app.route('/markers/<string:marker_name>')
def get_marker(marker_name):
    markers_collection = get_mongodb().markers_collection
    marker = markers_collection.find_one({'Instance': marker_name})
    out_marker = marker
    if 'values' in marker:
        values = [(x['date'], x['value']) for x in marker['values']]
        values = sorted(values, key=lambda x:x[0])
    else:
        values = None

    return render_template('marker.html', marker = marker, values=values)

if __name__ == '__main__':
    app.run(debug=False)