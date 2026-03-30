import xml.etree.ElementTree as ET
import random
import copy
import sys
import re
import html
import io

def generate_id():
    return str(random.randint(1775000000000, 1779999999999))

def indent(elem, level=0):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

file_path = "ColruytV2.alp"
backup_path = "ColruytV2_backup.alp"

ET.register_namespace('', '')
try:
    tree = ET.parse(file_path)
except Exception as e:
    print(f"Error parsing XML: {e}")
    sys.exit(1)

root = tree.getroot()
model = root.find('Model')
classes = model.find('ActiveObjectClasses')

main_class = None
robot_class = None

for aoc in classes.findall('ActiveObjectClass'):
    name_el = aoc.find('Name')
    if name_el is not None:
        if name_el.text == 'Main':
            main_class = aoc
        elif name_el.text == 'Robot':
            robot_class = aoc

if not main_class or not robot_class:
    print("Could not find Main or Robot classes.")
    sys.exit(1)

print("Found Main and Robot.")

# 1. Main: Add deliveryMode Parameter
main_vars = main_class.find('Variables')
if main_vars is None:
    main_vars = ET.SubElement(main_class, 'Variables')

has_del_mode = any(v.find('Name') is not None and v.find('Name').text == 'deliveryMode' for v in main_vars.findall('Variable'))
if not has_del_mode:
    var_el = ET.SubElement(main_vars, 'Variable', {'Class': 'Parameter'})
    ET.SubElement(var_el, 'Id').text = generate_id()
    ET.SubElement(var_el, 'Name').text = 'deliveryMode'
    ET.SubElement(var_el, 'X').text = '50'
    ET.SubElement(var_el, 'Y').text = '50'
    label_el = ET.SubElement(var_el, 'Label')
    ET.SubElement(label_el, 'X').text = '10'
    ET.SubElement(label_el, 'Y').text = '0'
    ET.SubElement(var_el, 'PublicFlag').text = 'false'
    ET.SubElement(var_el, 'PresentationFlag').text = 'true'
    ET.SubElement(var_el, 'ShowLabel').text = 'true'
    
    props = ET.SubElement(var_el, 'Properties', {'SaveInSnapshot': 'true', 'ModificatorType': 'STATIC'})
    ET.SubElement(props, 'Type').text = 'int'
    ET.SubElement(props, 'UnitType').text = 'NONE'
    ET.SubElement(props, 'SdArray').text = 'false'
    default_val = ET.SubElement(props, 'DefaultValue', {'Class': 'CodeValue'})
    ET.SubElement(default_val, 'Code').text = '0'
    
    param_edit = ET.SubElement(props, 'ParameterEditor')
    ET.SubElement(param_edit, 'Id').text = generate_id()
    ET.SubElement(param_edit, 'EditorContolType').text = 'TEXT_BOX'
    ET.SubElement(param_edit, 'MinSliderValue').text = '0'
    ET.SubElement(param_edit, 'MaxSliderValue').text = '100'
    ET.SubElement(param_edit, 'DelimeterType').text = 'NO_DELIMETER'

# 2. Main StartupCode injection
startup_code_el = main_class.find('StartupCode')
if startup_code_el is not None:
    code = startup_code_el.text or ""
    if 'robot.parDeliveryMode' not in code:
        code += "\n// Robot starts at node1 — fixed depot\nrobot.setXY(node1.getX(), node1.getY());\nrobot.parDeliveryMode = deliveryMode;\n"
        startup_code_el.text = code

# 3. Add Parameters to Robot
robot_vars = robot_class.find('Variables')
if robot_vars is None:
    robot_vars = ET.SubElement(robot_class, 'Variables')

def add_robot_param(name, ttype, default_code):
    has_param = any(v.find('Name') is not None and v.find('Name').text == name for v in robot_vars.findall('Variable'))
    if not has_param:
        var_el = ET.SubElement(robot_vars, 'Variable', {'Class': 'Parameter' if name.startswith('par') else 'PlainVariable'})
        ET.SubElement(var_el, 'Id').text = generate_id()
        ET.SubElement(var_el, 'Name').text = name
        ET.SubElement(var_el, 'X').text = '50'
        ET.SubElement(var_el, 'Y').text = str(150 + len(robot_vars)*30)
        label = ET.SubElement(var_el, 'Label')
        ET.SubElement(label, 'X').text = '10'
        ET.SubElement(label, 'Y').text = '0'
        ET.SubElement(var_el, 'PublicFlag').text = 'false'
        ET.SubElement(var_el, 'PresentationFlag').text = 'true'
        ET.SubElement(var_el, 'ShowLabel').text = 'true'
        
        if name.startswith('par'):
            props = ET.SubElement(var_el, 'Properties', {'SaveInSnapshot': 'true', 'ModificatorType': 'STATIC'})
            ET.SubElement(props, 'Type').text = ttype
            ET.SubElement(props, 'UnitType').text = 'NONE'
            ET.SubElement(props, 'SdArray').text = 'false'
            if default_code:
                dv = ET.SubElement(props, 'DefaultValue', {'Class': 'CodeValue'})
                ET.SubElement(dv, 'Code').text = default_code
            param_edit = ET.SubElement(props, 'ParameterEditor')
            ET.SubElement(param_edit, 'Id').text = generate_id()
            ET.SubElement(param_edit, 'EditorContolType').text = 'TEXT_BOX'
            ET.SubElement(param_edit, 'MinSliderValue').text = '0'
            ET.SubElement(param_edit, 'MaxSliderValue').text = '100'
            ET.SubElement(param_edit, 'DelimeterType').text = 'NO_DELIMETER'
        else:
            props = ET.SubElement(var_el, 'Properties', {'SaveInSnapshot': 'true', 'Constant': 'false', 'AccessType': 'public', 'StaticVariable': 'false'})
            ET.SubElement(props, 'Type').text = ttype
            if default_code:
                dv = ET.SubElement(props, 'InitialValue', {'Class': 'CodeValue'})
                ET.SubElement(dv, 'Code').text = default_code

add_robot_param('parStartNode', 'NodeLoc', 'new NodeLoc(main.node1.getX(), main.node1.getY())')
add_robot_param('parDestinationNode', 'NodeLoc', 'null')
add_robot_param('parDeliveryMode', 'int', '0')
add_robot_param('ordersCompleted', 'int', '0')

# Path arrays
add_robot_param('plannedRoute', 'java.util.List<NodeLoc>', 'new java.util.ArrayList<>()')
add_robot_param('routeLines', 'java.util.List<com.anylogic.engine.presentation.ShapeLine>', 'new java.util.ArrayList<>()')

# Update embedded robot in main
embedded = main_class.find('EmbeddedObjects')
if embedded is not None:
    for obj in embedded.findall('EmbeddedObject'):
        name = obj.find('Name')
        if name is not None and name.text == 'robot':
            params = obj.find('Parameters')
            if params is not None:
                def add_emb_param(pname):
                    found = any(p.find('Name') is not None and p.find('Name').text == pname for p in params.findall('Parameter'))
                    if not found:
                        p = ET.SubElement(params, 'Parameter')
                        ET.SubElement(p, 'Name').text = pname
                add_emb_param('parStartNode')
                add_emb_param('parDestinationNode')
                add_emb_param('parDeliveryMode')

# 3.5. Add Ovals to Main Presentation
pres = main_class.find('Presentation')
if pres is None:
    pres = ET.SubElement(main_class, 'Presentation')
level = pres.find('Level')
if level is None:
    # AnyLogic usually has Level inside Presentation
    level = ET.SubElement(pres, 'Level')

if level is not None:
    lpres = level.find('Presentation')
    if lpres is None:
        lpres = ET.SubElement(level, 'Presentation')
    
    if not any(t.find('Name') is not None and t.find('Name').text == 'textModeToggle' for t in lpres.findall('Text')):
        txt = ET.SubElement(lpres, 'Text')
        ET.SubElement(txt, 'Id').text = generate_id()
        ET.SubElement(txt, 'Name').text = 'textModeToggle'
        ET.SubElement(txt, 'X').text = '30'
        ET.SubElement(txt, 'Y').text = '30'
        l_t = ET.SubElement(txt, 'Label'); ET.SubElement(l_t, 'X').text='0'; ET.SubElement(l_t, 'Y').text='-10'
        ET.SubElement(txt, 'PublicFlag').text = 'true'
        ET.SubElement(txt, 'PresentationFlag').text = 'true'
        ET.SubElement(txt, 'ShowLabel').text = 'false'
        ET.SubElement(txt, 'DrawMode').text = 'SHAPE_DRAW_2D'
        ET.SubElement(txt, 'EmbeddedIcon').text = 'false'
        ET.SubElement(txt, 'Z').text = '0'
        ET.SubElement(txt, 'Rotation').text = '0.0'
        ET.SubElement(txt, 'Color').text = '-16776961'
        ET.SubElement(txt, 'Text').text = '"[ CLICK TO TOGGLE MODE ]\\nCurrent: " + (deliveryMode == 0 ? "CENTRE" : "RING ROAD")'
        font = ET.SubElement(txt, 'Font')
        ET.SubElement(font, 'Name').text = 'SansSerif'
        ET.SubElement(font, 'Size').text = '18'
        ET.SubElement(font, 'Style').text = '1'
        ET.SubElement(txt, 'Alignment').text = 'LEFT'
        ET.SubElement(txt, 'OnClickCode').text = 'deliveryMode = (deliveryMode == 0) ? 1 : 0;'

    # Check if ovalStart exists
    if not any(o.find('Name') is not None and o.find('Name').text == 'ovalStart' for o in lpres.findall('Oval')):
        os = ET.SubElement(lpres, 'Oval')
        ET.SubElement(os, 'Id').text = generate_id()
        ET.SubElement(os, 'Name').text = 'ovalStart'
        ET.SubElement(os, 'X').text = '0'; ET.SubElement(os, 'Y').text = '0'
        lbl = ET.SubElement(os, 'Label'); ET.SubElement(lbl, 'X').text = '0'; ET.SubElement(lbl, 'Y').text = '0'
        ET.SubElement(os, 'PublicFlag').text = 'true'
        ET.SubElement(os, 'PresentationFlag').text = 'true'
        ET.SubElement(os, 'ShowLabel').text = 'false'
        ET.SubElement(os, 'DrawMode').text = 'SHAPE_DRAW_2D3D'
        ET.SubElement(os, 'EmbeddedIcon').text = 'false'
        ET.SubElement(os, 'Z').text = '0'
        ET.SubElement(os, 'ZHeight').text = '10'
        ET.SubElement(os, 'LineWidth').text = '2'
        ET.SubElement(os, 'LineColor').text = '-16777216' # Black
        ET.SubElement(os, 'LineStyle').text = 'SOLID'
        ET.SubElement(os, 'RadiusX').text = '8'
        ET.SubElement(os, 'RadiusY').text = '8'
        ET.SubElement(os, 'Rotation').text = '0.0'
        ET.SubElement(os, 'FillColor').text = '-16711936' # Green
        
        od = ET.SubElement(lpres, 'Oval')
        ET.SubElement(od, 'Id').text = generate_id()
        ET.SubElement(od, 'Name').text = 'ovalDest'
        ET.SubElement(od, 'X').text = '0'; ET.SubElement(od, 'Y').text = '0'
        lbl = ET.SubElement(od, 'Label'); ET.SubElement(lbl, 'X').text = '0'; ET.SubElement(lbl, 'Y').text = '0'
        ET.SubElement(od, 'PublicFlag').text = 'true'
        ET.SubElement(od, 'PresentationFlag').text = 'true'
        ET.SubElement(od, 'ShowLabel').text = 'false'
        ET.SubElement(od, 'DrawMode').text = 'SHAPE_DRAW_2D3D'
        ET.SubElement(od, 'EmbeddedIcon').text = 'false'
        ET.SubElement(od, 'Z').text = '0'
        ET.SubElement(od, 'ZHeight').text = '10'
        ET.SubElement(od, 'LineWidth').text = '2'
        ET.SubElement(od, 'LineColor').text = '-16777216'
        ET.SubElement(od, 'LineStyle').text = 'SOLID'
        ET.SubElement(od, 'RadiusX').text = '8'
        ET.SubElement(od, 'RadiusY').text = '8'
        ET.SubElement(od, 'Rotation').text = '0.0'
        ET.SubElement(od, 'FillColor').text = '-65536' # Red

# 4. Functions
robot_funcs = robot_class.find('Functions')
if robot_funcs is None:
    robot_funcs = ET.SubElement(robot_class, 'Functions')

for f in list(robot_funcs.findall('Function')):
    nm = f.find('Name')
    if nm is not None and nm.text in ('findClosestNode', 'chooseNextNode'):
        robot_funcs.remove(f)

f1 = ET.SubElement(robot_funcs, 'Function', {'AccessType': 'default', 'StaticFunction': 'false'})
ET.SubElement(f1, 'ReturnModificator').text = 'RETURNS_VALUE'
ET.SubElement(f1, 'ReturnType').text = 'NodeLoc'
ET.SubElement(f1, 'Id').text = generate_id()
ET.SubElement(f1, 'Name').text = 'findClosestNode'
ET.SubElement(f1, 'X').text = '50'
ET.SubElement(f1, 'Y').text = '300'
l1 = ET.SubElement(f1, 'Label'); ET.SubElement(l1, 'X').text = '10'; ET.SubElement(l1, 'Y').text = '0'
ET.SubElement(f1, 'PublicFlag').text = 'false'
ET.SubElement(f1, 'PresentationFlag').text = 'true'
ET.SubElement(f1, 'ShowLabel').text = 'true'
p1 = ET.SubElement(f1, 'Parameter')
ET.SubElement(p1, 'Name').text = 'x'
ET.SubElement(p1, 'Type').text = 'double'
p2 = ET.SubElement(f1, 'Parameter')
ET.SubElement(p2, 'Name').text = 'y'
ET.SubElement(p2, 'Type').text = 'double'
ET.SubElement(f1, 'Body').text = """NodeLoc closest = null;
double best = Double.MAX_VALUE;
for (NodeLoc n : main.globalNodes) {
    double d = Math.sqrt(Math.pow(n.x - x, 2) + Math.pow(n.y - y, 2));
    if (d < best) { best = d; closest = n; }
}
return closest;"""

f2 = ET.SubElement(robot_funcs, 'Function', {'AccessType': 'default', 'StaticFunction': 'false'})
ET.SubElement(f2, 'ReturnModificator').text = 'RETURNS_VALUE'
ET.SubElement(f2, 'ReturnType').text = 'java.util.List<NodeLoc>'
ET.SubElement(f2, 'Id').text = generate_id()
ET.SubElement(f2, 'Name').text = 'calculatePath'
ET.SubElement(f2, 'X').text = '50'
ET.SubElement(f2, 'Y').text = '330'
l2 = ET.SubElement(f2, 'Label'); ET.SubElement(l2, 'X').text = '10'; ET.SubElement(l2, 'Y').text = '0'
ET.SubElement(f2, 'PublicFlag').text = 'false'
ET.SubElement(f2, 'PresentationFlag').text = 'true'
ET.SubElement(f2, 'ShowLabel').text = 'true'
p3 = ET.SubElement(f2, 'Parameter'); ET.SubElement(p3, 'Name').text = 'start'; ET.SubElement(p3, 'Type').text = 'NodeLoc'
p4 = ET.SubElement(f2, 'Parameter'); ET.SubElement(p4, 'Name').text = 'end'; ET.SubElement(p4, 'Type').text = 'NodeLoc'
p5 = ET.SubElement(f2, 'Parameter'); ET.SubElement(p5, 'Name').text = 'mode'; ET.SubElement(p5, 'Type').text = 'int'
ET.SubElement(f2, 'Body').text = """java.util.List<NodeLoc> path = new java.util.ArrayList<>();
if (start == null || end == null) return path;

NodeLoc sNode = findClosestNode(start.x, start.y);
NodeLoc eNode = findClosestNode(end.x, end.y);

if (sNode == null || eNode == null) return path;

java.util.Map<NodeLoc, Double> dist = new java.util.HashMap<>();
java.util.Map<NodeLoc, NodeLoc> prev = new java.util.HashMap<>();
java.util.List<NodeLoc> unvisited = new java.util.ArrayList<>(main.globalNodes);

for (NodeLoc n : unvisited) {
    dist.put(n, Double.MAX_VALUE);
    prev.put(n, null);
}
dist.put(sNode, 0.0);

while (!unvisited.isEmpty()) {
    NodeLoc u = null;
    double md = Double.MAX_VALUE;
    for (NodeLoc n : unvisited) {
        if (dist.get(n) < md) {
            md = dist.get(n);
            u = n;
        }
    }
    
    if (u == null || dist.get(u) == Double.MAX_VALUE) break;
    if (u == eNode) break;
    unvisited.remove(u);
    
    for (NodeLoc.Edge e : u.edges) {
        NodeLoc v = e.target;
        if (!unvisited.contains(v)) continue;
        
        double cost = Math.sqrt(Math.pow(v.x - u.x, 2) + Math.pow(v.y - u.y, 2));
        if (mode == 1) cost *= (1.0 + (v.crowdedness * 0.5));
        
        double alt = dist.get(u) + cost;
        if (alt < dist.get(v)) {
            dist.put(v, alt);
            prev.put(v, u);
        }
    }
}

NodeLoc curr = eNode;
while (curr != null && curr != sNode) {
    path.add(0, curr);
    curr = prev.get(curr);
}

if (curr == null) {
    path.clear();
    path.add(end);
}

return path;"""

f3 = ET.SubElement(robot_funcs, 'Function', {'AccessType': 'default', 'StaticFunction': 'false'})
ET.SubElement(f3, 'ReturnModificator').text = 'VOID'
ET.SubElement(f3, 'ReturnType').text = 'void'
ET.SubElement(f3, 'Id').text = generate_id()
ET.SubElement(f3, 'Name').text = 'drawRoute'
ET.SubElement(f3, 'X').text = '50'; ET.SubElement(f3, 'Y').text = '360'
l3 = ET.SubElement(f3, 'Label'); ET.SubElement(l3, 'X').text = '10'; ET.SubElement(l3, 'Y').text = '0'
ET.SubElement(f3, 'PublicFlag').text = 'false'
ET.SubElement(f3, 'PresentationFlag').text = 'true'
ET.SubElement(f3, 'ShowLabel').text = 'true'
p6 = ET.SubElement(f3, 'Parameter'); ET.SubElement(p6, 'Name').text = 'path'; ET.SubElement(p6, 'Type').text = 'java.util.List<NodeLoc>'
p7 = ET.SubElement(f3, 'Parameter'); ET.SubElement(p7, 'Name').text = 'source'; ET.SubElement(p7, 'Type').text = 'NodeLoc'
p8 = ET.SubElement(f3, 'Parameter'); ET.SubElement(p8, 'Name').text = 'color'; ET.SubElement(p8, 'Type').text = 'java.awt.Paint'
ET.SubElement(f3, 'Body').text = """clearRoute();
if (path == null || path.isEmpty() || source == null) return;
NodeLoc last = source;
for (NodeLoc n : path) {
    com.anylogic.engine.presentation.ShapeLine line = new com.anylogic.engine.presentation.ShapeLine();
    line.setX(last.x); line.setY(last.y);
    line.setDx(n.x - last.x); line.setDy(n.y - last.y);
    line.setLineWidth(3.0);
    line.setColor(color);
    routeLines.add(line);
    main.presentation.add(line);
    last = n;
}"""

f4 = ET.SubElement(robot_funcs, 'Function', {'AccessType': 'default', 'StaticFunction': 'false'})
ET.SubElement(f4, 'ReturnModificator').text = 'VOID'
ET.SubElement(f4, 'ReturnType').text = 'void'
ET.SubElement(f4, 'Id').text = generate_id()
ET.SubElement(f4, 'Name').text = 'clearRoute'
ET.SubElement(f4, 'X').text = '50'; ET.SubElement(f4, 'Y').text = '390'
l4 = ET.SubElement(f4, 'Label'); ET.SubElement(l4, 'X').text = '10'; ET.SubElement(l4, 'Y').text = '0'
ET.SubElement(f4, 'PublicFlag').text = 'false'
ET.SubElement(f4, 'PresentationFlag').text = 'true'
ET.SubElement(f4, 'ShowLabel').text = 'true'
ET.SubElement(f4, 'Body').text = """for (com.anylogic.engine.presentation.ShapeLine line : routeLines) {
    main.presentation.remove(line);
}
routeLines.clear();"""

# 4.5. Add pollEvent to Robot to trigger onChange()
revents = robot_class.find('Events')
if revents is None:
    revents = ET.SubElement(robot_class, 'Events')

if not any(ev.find('Name') is not None and ev.find('Name').text == 'pollEvent' for ev in revents.findall('Event')):
    ev_el = ET.SubElement(revents, 'Event')
    ET.SubElement(ev_el, 'Id').text = generate_id()
    ET.SubElement(ev_el, 'Name').text = 'pollEvent'
    ET.SubElement(ev_el, 'X').text = '50'; ET.SubElement(ev_el, 'Y').text = '400'
    lbl = ET.SubElement(ev_el, 'Label'); ET.SubElement(lbl, 'X').text = '10'; ET.SubElement(lbl, 'Y').text = '0'
    ET.SubElement(ev_el, 'PublicFlag').text = 'false'
    ET.SubElement(ev_el, 'PresentationFlag').text = 'true'
    ET.SubElement(ev_el, 'ShowLabel').text = 'true'
    
    props = ET.SubElement(ev_el, 'Properties', {'TriggerType': 'timeout', 'Mode': 'cyclic'})
    to = ET.SubElement(props, 'Timeout', {'Class': 'CodeUnitValue'})
    ET.SubElement(to, 'Code').text = '0.5'
    ET.SubElement(to, 'Unit', {'Class': 'TimeUnits'}).text = 'SECOND'
    
    rt = ET.SubElement(props, 'Rate', {'Class': 'CodeUnitValue'})
    ET.SubElement(rt, 'Code').text = '1'
    ET.SubElement(rt, 'Unit', {'Class': 'RateUnits'}).text = 'PER_SECOND'
    
    ET.SubElement(props, 'OccurrenceAtTime').text = 'true'
    ET.SubElement(props, 'OccurrenceDate').text = '1778000000000'
    
    ot = ET.SubElement(props, 'OccurrenceTime', {'Class': 'CodeUnitValue'})
    ET.SubElement(ot, 'Code').text = '0'
    ET.SubElement(ot, 'Unit', {'Class': 'TimeUnits'}).text = 'SECOND'
    
    rc = ET.SubElement(props, 'RecurrenceCode', {'Class': 'CodeUnitValue'})
    ET.SubElement(rc, 'Code').text = '0.5'
    ET.SubElement(rc, 'Unit', {'Class': 'TimeUnits'}).text = 'SECOND'
    
    ET.SubElement(props, 'Condition').text = 'false'
    ET.SubElement(ev_el, 'Action').text = 'onChange();'

# 5. Rework StatechartElements
sce = robot_class.find('StatechartElements')
if sce is not None:
    # Safely clear old states and transitions, keep entry point
    elements = list(sce)
    entry_point = None
    for el in elements:
        if el.get('Class') == 'EntryPoint':
            entry_point = el
    
    sce.clear()
    
    # Re-insert EntryPoint
    if entry_point is not None:
        sce.append(entry_point)

    id_in = generate_id()
    id_pu = generate_id()
    id_dl = generate_id()
    id_rt = generate_id()
    id_cp = generate_id()

    if entry_point is not None:
        props = entry_point.find('Properties')
        if props is not None:
            props.set('Target', id_in)
            action = props.find('Action')
            if action is not None:
                action.text = '' 
            
    # stInit (Delay state)
    si = ET.SubElement(sce, 'StatechartElement', {'Class': 'State', 'ParentState': 'ROOT_NODE'})
    ET.SubElement(si, 'Id').text = id_in
    ET.SubElement(si, 'Name').text = 'stInit'
    ET.SubElement(si, 'X').text = '300'
    ET.SubElement(si, 'Y').text = '80'
    l_in = ET.SubElement(si, 'Label'); ET.SubElement(l_in, 'X').text = '10'; ET.SubElement(l_in, 'Y').text = '10'
    ET.SubElement(si, 'PublicFlag').text = 'false'
    ET.SubElement(si, 'PresentationFlag').text = 'true'
    ET.SubElement(si, 'ShowLabel').text = 'true'
    props_in = ET.SubElement(si, 'Properties', {'Width': '100', 'Height': '50'})
    ET.SubElement(props_in, 'FillColor').text = '-10496'
    
    # stPickup
    sp1 = ET.SubElement(sce, 'StatechartElement', {'Class': 'State', 'ParentState': 'ROOT_NODE'})
    ET.SubElement(sp1, 'Id').text = id_pu
    ET.SubElement(sp1, 'Name').text = 'stPickup'
    ET.SubElement(sp1, 'X').text = '300'
    ET.SubElement(sp1, 'Y').text = '150'
    l1 = ET.SubElement(sp1, 'Label'); ET.SubElement(l1, 'X').text = '10'; ET.SubElement(l1, 'Y').text = '10'
    ET.SubElement(sp1, 'PublicFlag').text = 'false'
    ET.SubElement(sp1, 'PresentationFlag').text = 'true'
    ET.SubElement(sp1, 'ShowLabel').text = 'true'
    props_pu = ET.SubElement(sp1, 'Properties', {'Width': '100', 'Height': '50'})
    ET.SubElement(props_pu, 'FillColor').text = '-10496'
    ET.SubElement(props_pu, 'EntryAction').text = """// Snap to depot
setXY(parStartNode.x, parStartNode.y);
goalNode = parStartNode;

// Pick a random destination (different from start)
java.util.List<NodeLoc> candidates = new java.util.ArrayList<>();
for (NodeLoc n : main.globalNodes) {
    if (n == null || parStartNode == null) continue;
    double dist = Math.sqrt(
        Math.pow(n.x - parStartNode.x, 2) +
        Math.pow(n.y - parStartNode.y, 2));
    if (dist > 80) candidates.add(n);  // must be far enough
}
if (candidates.isEmpty()) candidates.addAll(main.globalNodes);
if (!candidates.isEmpty()) {
    parDestinationNode = candidates.get((int)(Math.random() * candidates.size()));
    traceln("New delivery → destination: " + parDestinationNode.x + ", " + parDestinationNode.y);
    main.ovalStart.setX(parStartNode.x);
    main.ovalStart.setY(parStartNode.y);
    main.ovalDest.setX(parDestinationNode.x);
    main.ovalDest.setY(parDestinationNode.y);
    
    // Dijkstra path calculation
    plannedRoute = calculatePath(parStartNode, parDestinationNode, parDeliveryMode);
    drawRoute(plannedRoute, parStartNode, java.awt.Color.BLUE);
}"""

    # stDeliver
    sp2 = ET.SubElement(sce, 'StatechartElement', {'Class': 'State', 'ParentState': 'ROOT_NODE'})
    ET.SubElement(sp2, 'Id').text = id_dl
    ET.SubElement(sp2, 'Name').text = 'stDeliver'
    ET.SubElement(sp2, 'X').text = '300'
    ET.SubElement(sp2, 'Y').text = '250'
    l2 = ET.SubElement(sp2, 'Label'); ET.SubElement(l2, 'X').text = '10'; ET.SubElement(l2, 'Y').text = '10'
    ET.SubElement(sp2, 'PublicFlag').text = 'false'
    ET.SubElement(sp2, 'PresentationFlag').text = 'true'
    ET.SubElement(sp2, 'ShowLabel').text = 'true'
    props_dl = ET.SubElement(sp2, 'Properties', {'Width': '100', 'Height': '50'})
    ET.SubElement(props_dl, 'FillColor').text = '-10496'
    ET.SubElement(props_dl, 'EntryAction').text = """if (parDestinationNode == null) return;

if (plannedRoute != null && !plannedRoute.isEmpty()) {
    NodeLoc nextNode = plannedRoute.remove(0);
    goalNode = nextNode;
    moveTo(nextNode.x, nextNode.y);
}"""

    # stReturn
    sp3 = ET.SubElement(sce, 'StatechartElement', {'Class': 'State', 'ParentState': 'ROOT_NODE'})
    ET.SubElement(sp3, 'Id').text = id_rt
    ET.SubElement(sp3, 'Name').text = 'stReturn'
    ET.SubElement(sp3, 'X').text = '450'
    ET.SubElement(sp3, 'Y').text = '250'
    l3 = ET.SubElement(sp3, 'Label'); ET.SubElement(l3, 'X').text = '10'; ET.SubElement(l3, 'Y').text = '10'
    ET.SubElement(sp3, 'PublicFlag').text = 'false'
    ET.SubElement(sp3, 'PresentationFlag').text = 'true'
    ET.SubElement(sp3, 'ShowLabel').text = 'true'
    props_rt = ET.SubElement(sp3, 'Properties', {'Width': '100', 'Height': '50'})
    ET.SubElement(props_rt, 'FillColor').text = '-10496'
    ET.SubElement(props_rt, 'EntryAction').text = """if (parStartNode == null) return;

if (plannedRoute == null || plannedRoute.isEmpty()) {
    plannedRoute = calculatePath(findClosestNode(getX(), getY()), parStartNode, parDeliveryMode);
    drawRoute(plannedRoute, findClosestNode(getX(), getY()), java.awt.Color.RED);
}

if (plannedRoute != null && !plannedRoute.isEmpty()) {
    NodeLoc nextNode = plannedRoute.remove(0);
    goalNode = nextNode;
    moveTo(nextNode.x, nextNode.y);
}"""

    # stComplete
    sp4 = ET.SubElement(sce, 'StatechartElement', {'Class': 'State', 'ParentState': 'ROOT_NODE'})
    ET.SubElement(sp4, 'Id').text = id_cp
    ET.SubElement(sp4, 'Name').text = 'stComplete'
    ET.SubElement(sp4, 'X').text = '450'
    ET.SubElement(sp4, 'Y').text = '150'
    l4 = ET.SubElement(sp4, 'Label'); ET.SubElement(l4, 'X').text = '10'; ET.SubElement(l4, 'Y').text = '10'
    ET.SubElement(sp4, 'PublicFlag').text = 'false'
    ET.SubElement(sp4, 'PresentationFlag').text = 'true'
    ET.SubElement(sp4, 'ShowLabel').text = 'true'
    props_cp = ET.SubElement(sp4, 'Properties', {'Width': '100', 'Height': '50'})
    ET.SubElement(props_cp, 'FillColor').text = '-10496'
    ET.SubElement(props_cp, 'EntryAction').text = """clearRoute();
ordersCompleted++;
traceln("Order #" + ordersCompleted + " complete at time " + time());
main.ovalStart.setX(-100);
main.ovalDest.setX(-100); // hide them offscreen
parDestinationNode = null;"""

    def add_transition(id_src, id_dst, trigger_type, timeout_code, cond_code, pts, name='t'):
        t_el = ET.SubElement(sce, 'StatechartElement', {'Class': 'Transition', 'ParentState': 'ROOT_NODE'})
        ET.SubElement(t_el, 'Id').text = generate_id()
        ET.SubElement(t_el, 'Name').text = name
        ET.SubElement(t_el, 'X').text = str(pts[0][0])
        ET.SubElement(t_el, 'Y').text = str(pts[0][1])
        lbl = ET.SubElement(t_el, 'Label'); ET.SubElement(lbl, 'X').text = '10'; ET.SubElement(lbl, 'Y').text = '0'
        ET.SubElement(t_el, 'PublicFlag').text = 'false'
        ET.SubElement(t_el, 'PresentationFlag').text = 'true'
        ET.SubElement(t_el, 'ShowLabel').text = 'false'
        pts_el = ET.SubElement(t_el, 'Points')
        for i, (px, py) in enumerate(pts):
            pt_el = ET.SubElement(pts_el, 'Point')
            ET.SubElement(pt_el, 'X').text = str(px - pts[0][0])  # AnyLogic often uses relative coordinates for points after first ? No, generally Point X/Y are relative offsets? No wait, points in transitions are usually relative to the Transition X, Y. The first point is often 0,0.
            ET.SubElement(pt_el, 'Y').text = str(py - pts[0][1])
        ET.SubElement(t_el, 'IconOffset').text = '20.0'
        
        props = ET.SubElement(t_el, 'Properties', {'Source': id_src, 'Target': id_dst, 'Trigger': trigger_type})
        if timeout_code:
            to = ET.SubElement(props, 'Timeout', {'Class': 'CodeUnitValue'})
            ET.SubElement(to, 'Code').text = timeout_code
            ET.SubElement(to, 'Unit', {'Class': 'TimeUnits'}).text = 'SECOND'
        if cond_code:
            ET.SubElement(props, 'Condition').text = cond_code
        rt = ET.SubElement(props, 'Rate', {'Class': 'CodeUnitValue'})
        ET.SubElement(rt, 'Code').text = '1'
        ET.SubElement(rt, 'Unit', {'Class': 'RateUnits'}).text = 'PER_SECOND'
        ET.SubElement(props, 'MessageType').text = 'Object'
        ET.SubElement(props, 'DefaultTransition').text = 'true'
        ET.SubElement(props, 'FilterType').text = 'unconditionally'
        ET.SubElement(props, 'EqualsExpression').text = '"text"'
        ET.SubElement(props, 'SatisfiesExpression').text = 'true'

    # Transitions
    add_transition(id_in, id_pu, 'timeout', '0.1', None, [(350, 130), (350, 150)], 'trInitPickup')
    add_transition(id_pu, id_dl, 'timeout', '0.1', None, [(350, 200), (350, 250)], 'trPickupDeliver')
    add_transition(id_dl, id_rt, 'condition', None, 'plannedRoute.isEmpty() && goalNode != null && Math.sqrt(Math.pow(goalNode.x - getX(),2) + Math.pow(goalNode.y - getY(),2)) < 5.0 && Math.sqrt(Math.pow(parDestinationNode.x - getX(), 2) + Math.pow(parDestinationNode.y - getY(), 2)) < 8.0', [(400, 275), (450, 275)], 'trDeliverReturn')
    add_transition(id_dl, id_dl, 'condition', None, '!plannedRoute.isEmpty() && goalNode != null && Math.sqrt(Math.pow(goalNode.x - getX(),2) + Math.pow(goalNode.y - getY(),2)) < 5.0', [(350, 300), (330, 320), (370, 320), (350, 300)], 'trDeliverLoop')

    add_transition(id_rt, id_cp, 'condition', None, 'plannedRoute.isEmpty() && goalNode != null && Math.sqrt(Math.pow(goalNode.x - getX(),2) + Math.pow(goalNode.y - getY(),2)) < 5.0 && Math.sqrt(Math.pow(parStartNode.x - getX(), 2) + Math.pow(parStartNode.y - getY(), 2)) < 8.0', [(500, 250), (500, 200)], 'trReturnComplete')
    add_transition(id_rt, id_rt, 'condition', None, '!plannedRoute.isEmpty() && goalNode != null && Math.sqrt(Math.pow(goalNode.x - getX(),2) + Math.pow(goalNode.y - getY(),2)) < 5.0', [(500, 300), (480, 320), (520, 320), (500, 300)], 'trReturnLoop')

    add_transition(id_cp, id_pu, 'timeout', '1', None, [(450, 175), (400, 175)], 'trCompletePickup')

indent(root)

stream = io.StringIO()
tree.write(stream, encoding='unicode', xml_declaration=False)
xml_str = stream.getvalue()

# Replace inner text with explicitly specified CDATA handling using regex
cdata_tags = ['Action', 'EntryAction', 'Body', 'Code', 'Condition', 'StartupCode', 'Name', 'ClassName']

# Using lambda to unescape XML entities and wrap in CDATA manually.
def replacer(m):
    tag = m.group(1)
    # Get raw inner text representing HTML tags correctly encoded
    inner = m.group(2)
    # Skip if it is naturally empty
    if not inner.strip(): 
        return f"<{tag}></{tag}>"
    # Or if already contains CDATA marker (because we read it like that?)
    if '<![CDATA[' in inner:
        return f"<{tag}>{inner}</{tag}>"
    
    # Unescape ElementTree xml-encoded strings
    unescaped = html.unescape(inner)
    return f"<{tag}><![CDATA[{unescaped}]]></{tag}>"

pattern = re.compile(f'<({"|".join(cdata_tags)})>(.*?)</\\1>', flags=re.DOTALL)
final_xml = pattern.sub(replacer, xml_str)

# Prepend the AnyLogic header explicitly
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<!--\n*************************************************\n\t         AnyLogic Project File\n*************************************************\n-->\n')
    f.write(final_xml)

print("Successfully wrote updated AnyLogic XML!")
