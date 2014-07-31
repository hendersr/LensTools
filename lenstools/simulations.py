"""

.. module:: simulations 
	:platform: Unix
	:synopsis: This module handles the book keeping of a simulation set map names, cosmological parameters, etc...


.. moduleauthor:: Andrea Petri <apetri@phys.columbia.edu>


"""

from __future__ import division

from astropy.cosmology import FlatwCDM

######################################
###########IGS1 class#################
######################################

class IGS1(FlatwCDM):

	"""
	Class handler of the IGS1 simulations set, inherits the cosmological parameters from the astropy.cosmology.FlatwCDM class; the default parameter values are the fiducial ones

	"""

	#Don't touch these! 
	_series_name = "m"
	_num_particles = 512
	_box_size_mpc = 240
	_lens_plane_size = 4096


	def __init__(self,H0=70.0,Om0=0.26,w0=-1.0,sigma8=0.798,ns=0.960,root_path=None,name=None):

		super(IGS1,self).__init__(H0,Om0,w0=w0,name=name)
		self.sigma8 = sigma8
		self.ns = ns

		assert root_path is not None,"You must specify the root path of your IGS1 local copy!"

		self.root_path = root_path

		#Don't touch these! 
		self._cosmo_id_string =  "Om{0:.3f}_Ol{1:.3f}_w{2:.3f}_ns{3:.3f}_si{4:.3f}".format(self.Om0,1.0-self.Om0,self.w0,self.ns,self.sigma8)
		self._box_string = str(self._num_particles)+"b"+str(self._box_size_mpc)
		self._full_path = self.root_path.rstrip("/") + "/"+self._series_name+"-"+self._box_string+"_"+self._cosmo_id_string

	def __repr__(self):

		astropy_string = super(IGS1,self).__repr__()
		pieces = astropy_string.split(",")
		si8_piece = u" sigma8={0}".format(self.sigma8)
		ns_piece = u" ns={0}".format(self.ns)

		return ",".join(pieces[:3] + [si8_piece,ns_piece] + pieces[3:])

	def _plane_id(self,z):

		if z==1.0:
			return "0029p"
		elif z==1.5:
			return "0038p"
		elif z==2.0:
			return "0046p"
		else:
			raise ValueError("IGS1 doesn't have maps at redshift {0}".format(z))

	def getNames(self,realizations,z=1.0,kind="convergence",big_fiducial_set=False):

		"""
		Get the full name of the IGS1 maps, once a redshift, realization identificator and kind are specified

		:param z: redshift plane of the maps, must be one of [1.0,1.5,2.0]
		:type z: float.

		:param realizations: list of realizations to get the names of, the elements must be in [1,1000]
		:type realizations: list. or int.

		:param kind: decide if retrieve convergence or shear maps, must be one of [convergence,shear1,shear2]
		:type kind: str.

		:param big_fiducial_set: set to True if you want to get the names of the bigger fiducial simulation based on 45 N-body simulations
		:type big_fiducial_set: bool.

		"""

		assert type(realizations) == list or type(realizations) == int
		assert z in [1.0,1.5,2.0],"IGS1 doesn't have maps at redshift {0}".format(z)
		assert kind in ["convergence","shear1","shear2"],"You must select one of these: convergence,shear1,shear2"

		if kind=="convergence":
			prefix = "WL-conv"
			direct = "Maps"
		elif kind=="shear1":
			prefix = "Wl-shear1"
			direct = "shear"
		elif kind=="shear2":
			prefix = "Wl-shear2"
			direct = "shear"

		full_path = self._full_path

		if big_fiducial_set:
			assert self.Om0==0.26 and self.w0==-1.0 and self.sigma8==0.798 and self.ns==0.96
			full_path += "_f"

		full_path += "/{0}".format(direct)

		if type(realizations) == int:
			full_path + "/{0}_".format(prefix)+self._series_name+"-"+self._box_string+"_"+self._cosmo_id_string+"_"+str(self._lens_plane_size)+"xy_{0:0004d}r_{1}_{2:0004d}z_og.gre.fit".format(realizations,self._plane_id(z),int(z*100))
		else:
			return [full_path + "/{0}_".format(prefix)+self._series_name+"-"+self._box_string+"_"+self._cosmo_id_string+"_"+str(self._lens_plane_size)+"xy_{0:0004d}r_{1}_{2:0004d}z_og.gre.fit".format(r,self._plane_id(z),int(z*100)) for r in realizations]


################################
#######EMU1 class###############
################################

class CFHTemu1(IGS1):

	"""
	Class handler of the weak lensing CFHTemu1 simulations set, inherits from IGS1; this simulation suite contains 91 different cosmological models based on 1 N-body simulation each. Each model has 1000 realizations for each of the 13 CFHT subfields 

	"""

	#Don't touch these! 
	_series_name = "emu1"
	_num_particles = 512
	_box_size_mpc = 240

	def getNames(self,realizations,subfield=1,smoothing=0.5):

		"""
		Get the full name of the CFHT emu1 maps, once a subfield and smoothing scale are specified

		:param subfield: the specific CFHT subfield you want to retrieve, must be between 1 and 13
		:type subfield: int.

		:param smoothing: smoothing scale of the maps you wish to retrieve, in arcmin
		:type smoothing: float.

		:param realizations: list of realizations to get the names of, the elements must be in [1,1000]
		:type realizations: list. or int.

		"""

		assert 1 <= subfield <= 13
		assert type(realizations) == list or type(realizations) == int

		#Build the file name
		root_path = self.root_path

		name = root_path.rstrip("/") + "/" 
		name += self._series_name + "-" 
		name += self._box_string + "_" 
		name += self._cosmo_id_string 
		name += "/subfield{0}/".format(subfield) 
		name += "/sigma{0:02d}/".format(int(smoothing*10))
		name += "SIM_KS_sigma{0:02d}_subfield{1}_{2}-{3}_{4}_".format(int(smoothing*10),subfield,self._series_name,self._box_string,self._cosmo_id_string)

		#return the results
		if type(realizations) == int:
			return name + "{0:0004d}r.fit".format(realizations)
		else:
			return [name + "{0:0004d}r.fit".format(r) for r in realizations]









