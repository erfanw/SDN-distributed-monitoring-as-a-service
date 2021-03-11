controller:
	cp cpm/cpm_dynamic.py nfm/cpm_dynamic.py && cd nfm && ryu-manager collector.py cpm_dynamic.py topodsc.py topo_base.py

controller_sp:
	cd nfm && ryu-manager collector.py shortest_path.py topodsc.py topo_base.py

topk: 
	cp cpm/top_k.py nfm/top_k.py && cd nfm && ryu-manager collector.py top_k.py topodsc.py topo_base.py

topk_ac: 
	cp cpm/top_k_ac.py nfm/top_k.py && cd nfm && ryu-manager collector.py top_k.py topodsc.py topo_base.py

topo:
	cd topology && python3 topo_gen.py --gf testbed.json

test:
	cd topology && python3 topo_gen.py --test enable --gf testbed.json

clean:
	mn -c && rm nfm/cpm_dynamic.py

debug: 
	cp cpm/tunnel_ecmp.py nfm/shortest_path.py && cd nfm && ryu-manager collector.py shortest_path.py topodsc.py topo_base.py --verbose
	
database:
	python3 web/web_app.py 

test_st:
	cd topology && python3 topo_gen.py --gf stanford_tp.json --test enable
