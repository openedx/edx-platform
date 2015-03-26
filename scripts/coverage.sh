#!/bin/bash
 

case $1 in
   "shard1")	
	echo "Collecting Coverage for Bok-Choy Shard1"
	paver bokchoy_coverage 
	echo "Merging Coverage into a Single HTML File for Bok-Choy Shard1"
	python ./scripts/cov_merge.py bok_choy bok_choy_shard1_coverage.html	
	;;
   "shard2")
	echo "Collecting Coverage for Bok-Choy Shard2"
	paver bokchoy_coverage 
	echo "Merging Coverage into a Single HTML File for Bok-Choy Shard2"
	python ./scripts/cov_merge.py bok_choy bok_choy_shard2_coverage.html
	;;
   "shard3")
	echo "Collecting Coverage for Bok-Choy Shard3"
	paver bokchoy_coverage 
	echo "Merging Coverage into a Single HTML File for Bok-Choy Shard3"
	python ./scripts/cov_merge.py bok_choy bok_choy_shard3_coverage.html
	;;
   *)
	echo "Invalid Bok-Choy Shard Value!";;
esac
