# s2Cells API DOCS
# https://s2sphere.readthedocs.io/en/latest/api.html
# python -m pip install s2sphere
import s2sphere

# python -m pip install python-dateutil
from datetime import datetime
from dateutil import tz

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

import settings
LEVEL: int = 14
ALT = 0.
OUTPUT_KML = 'MHNbiome.kml'
STYLE_KML = 'S2CellsTemplate.kml'
BIOME = ['Forest', 'Desert', 'Swamp']
poly_styles = {'Forest':'#poly-7CB342-1200-76', 'Desert':'#poly-F9A825-1200-76', 'Swamp':'#poly-673AB7-1200-76'}
HILBELT = False

# KML Namespace
XMLNS = {'kmlns': 'http://www.opengis.net/kml/2.2'}

def main():

    # Get Day Count
    dt_utc = datetime.fromisoformat(settings.dt).astimezone(tz.gettz('UTC'))
    day_cnt = int(dt_utc.timestamp() / (24 * 60 * 60))

    # load kml template
    xml_tree = ET.parse("S2CellsTemplate.kml")
    ET.register_namespace('', XMLNS['kmlns'])
    kml_doc = xml_tree.find('kmlns:Document', XMLNS)
    kml_doc.find('kmlns:name', XMLNS).text = dt_utc.strftime('%Y-%m-%d')

    # Get Cell object
    r = s2sphere.RegionCoverer()
    r.max_level = LEVEL
    r.min_level = LEVEL
    p1 = s2sphere.LatLng.from_degrees(settings.rect[0][0], settings.rect[0][1])
    p2 = s2sphere.LatLng.from_degrees(settings.rect[1][0], settings.rect[1][1])

    cell_ids = r.get_covering(s2sphere.LatLngRect.from_point_pair(p1, p2))

    cid_pre = 0
    Hilbert_Curves = list()
    for cid in cell_ids:
        #  get Cell from CellId
        cell: Cell = s2sphere.Cell.from_face_pos_level(cid.face(), cid.pos(), cid.level())
        cll: LatLng = cid.to_lat_lng()

        # Habitat cell
        # get habitat id from cellid
        habitat_id = int((int(cell.id().to_token(), 16) + 1) / 2)
        # date shift
        habitat_idx = (habitat_id - day_cnt) % len(BIOME)
        # append habitat cell
        kml_doc.append(placemark_s2cells(cell, BIOME[habitat_idx]))

        # for test
        if HILBELT:
            # Draw Hilbert Curves
            cid_diff = int(cid.to_token(), 16) - cid_pre
            if cid_diff == 2:
                Hilbert_Curves.append([cll.lng().degrees, cll.lat().degrees])
            else:
                if len(Hilbert_Curves) > 0:
                    kml_doc.append(placemark_linestring(Hilbert_Curves))
                    Hilbert_Curves = list()
                    Hilbert_Curves.append([cll.lng().degrees, cll.lat().degrees])
            cid_pre = int(cid.to_token(), 16)

    if HILBELT and len(Hilbert_Curves) > 0:
        kml_doc.append(placemark_linestring(Hilbert_Curves))

    # indent document
    ET.indent(xml_tree)

    # write kmlfile
    xml_tree.write(OUTPUT_KML, encoding='UTF-8', xml_declaration=True)

def placemark_s2cells(cell: s2sphere.Cell, habitat):
    # add Polygon element
    placemark = ET.Element('Placemark')
    name = ET.SubElement(placemark, 'name')
    name.text = habitat
    desc = ET.SubElement(placemark, 'description')
    desc.text = cell.id().to_token()
    styleurl = ET.SubElement(placemark, 'styleUrl')
    styleurl.text = poly_styles[habitat]
    poly = ET.SubElement(placemark, 'Polygon')
    outerboundaryis = ET.SubElement(poly, 'outerBoundaryIs')
    linearring = ET.SubElement(outerboundaryis, 'LinearRing')
    tessellate = ET.SubElement(linearring, 'tessellate')
    tessellate.text = '1'
    altitudemode = ET.SubElement(linearring, 'altitudeMode')
    altitudemode.text = 'clampToGround'

    # draw cell vertex
    coordinates = ET.SubElement(linearring, 'coordinates')
    indent = '\n' + ' ' * 14
    coord = ''
    for k in range(4):
        ll = s2sphere.LatLng.from_point(cell.get_vertex(k))
        coord = coord + indent + f'{ll.lng().degrees},{ll.lat().degrees},{ALT}'
    # close path
    ll = s2sphere.LatLng.from_point(cell.get_vertex(0))
    coord = coord + indent + f'{ll.lng().degrees},{ll.lat().degrees},{ALT}'
    coord = coord + '\n' + ' ' * 12
    coordinates.text = coord

    return placemark

def placemark_linestring(lines):
    # add Point element
    placemark = ET.Element('Placemark')

    linestring = ET.SubElement(placemark, 'LineString')
    coordinates = ET.SubElement(linestring, 'coordinates')

    indent = '\n' + ' ' * 10
    coord = ''
    for line in lines:
        coord = coord + indent + f'{line[0]}, {line[1]}, 0.'
    coord = coord + '\n' + ' ' * 8
    coordinates.text = coord

    return placemark

if __name__ == "__main__":
    main()
