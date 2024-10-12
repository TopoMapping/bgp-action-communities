## About Paper Inferences and Data

Inside the directory `paper` we list, per year (2018 to 2023), the specific RIBs for each collector we have used to 
infer the AS Squatters and BGP Action Communities. We also provide the list of the inferred BGP Action Communities
(`action_communities.txt`), the AS Squatters (`squatter_ases.txt`) and all the communities on BGP Dump that respect
the parameters of the algorithm (`all_communities_bgp.txt`), used to compute the statistics of the paper.

The Ground Truth is an expansion of others using the data from documentation, `whois`, public websites and NL Nog project.
We define two categories that were specialized in:

* Information Communities:
  * geolocation
  * private
  * exchange
  * route type
  * rpki
  * error
* Action Communities:
  * internal routes 
  * traffic engineering

And three levels of ASes in the Internet Hierarchy:

* Tier 1
* Tier 2
* Other Tiers
