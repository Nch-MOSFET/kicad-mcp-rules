import sys,os
src=open('build_board.py',encoding='utf-8').read()
src=src[:src.index("# ------------------------------------------------------------------ router")]
sys.argv=['x','vascular_age_meter/netlist.xml','pl_%s_%s_%s.kicad_pcb'%(os.environ.get('VAR','A'),os.environ['SEED'],os.environ['MARGIN']),'C:/Users/<user>/Documents/KiCad_work/vascular_age_meter']
exec(src)
pcbnew.SaveBoard(sys.argv[2],board)
print("DONE")
