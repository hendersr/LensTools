import types
import numpy as np
from astropy.cosmology import w0waCDM
from astropy.units import rad

try:
	from ..extern import _nicaea
	_nicaea=_nicaea
except ImportError:
	_nicaea=None


##########################################################
##########Nicaea built-in redshift distributions##########
##########################################################

_nicaea_builtin = dict()
_nicaea_builtin["ludo"] = 5
_nicaea_builtin["jonben"] = 5
_nicaea_builtin["ymmk"] = 5
_nicaea_builtin["single"] = 2
_nicaea_builtin["hist"] = 0

################################################################################
###########Useful to check validity of redshift distribution inputs#############
################################################################################

def _check_redshift(z,distribution,distribution_parameters,**kwargs):

	#Parse redshift distribution from input
	if type(z)==np.float:
			
		nzbins = 1
		nofz = ["single"]
		Nnz = np.array([2],dtype=np.int32)
		par_nz = np.array([z,z])

	elif type(distribution)==types.FunctionType:

		assert type(z)==np.ndarray and z.ndim==1,"distribution is a callable, hence z must be a one dimensional array!"
		
		if distribution_parameters is None:
			distribution_parameters="one"
		
		assert distribution_parameters in ["one","all"],"distribution is a callable, hence distribution_parameters must be either 'one' or 'all'"

		if distribution_parameters=="one":
			
			nzbins = 1
			nofz = ["hist"]
			Nnz = np.array([2*len(z)-1],dtype=np.int32)

			#Format paramaters accordingly
			midpoints = 0.5*(z[1:]+z[:-1])
			gal_in_bin = distribution(midpoints,**kwargs)
			par_nz = np.concatenate((np.array([z[0],z[-1]]),z[1:-1],gal_in_bin))
			assert len(par_nz)==Nnz[0]

		else:

			nzbins = len(z)-1
			nofz = ["hist"]*nzbins
			Nnz = np.ones(nzbins,dtype=np.int32)*3

			#Format paramaters accordingly
			midpoints = 0.5*(z[1:]+z[:-1])
			gal_in_bin = distribution(midpoints,**kwargs)
			par_nz = np.zeros(3*nzbins)

			for n in range(nzbins):
				par_nz[3*n] = z[n]
				par_nz[3*n+1] = z[n+1]
				par_nz[3*n+2] = gal_in_bin[n]

	else:
			
		assert z is None,"If you want to specify the distribution parameters manually z must be None"
		assert type(distribution)==list and type(distribution_parameters)==list,"If you want to specify the distribution parameters manually both distribution and distribution parameters must be lists"
		assert len(distribution)==len(distribution_parameters),"The lists must have the same length"

		nzbins = len(distribution)
		nofz = distribution
		Nnz = list()
			
		for n,distr_in_bin in enumerate(nofz):
				
			assert distr_in_bin in _nicaea_builtin.keys(),"{0} must be one of NICAEA built in types: {1}".format(distr_in_bin,_nicaea_builtin.keys())
			if distr_in_bin=="hist":

				#Check that number of parameters is odd to conform to standard
				assert len(distribution_parameters[n]%2==1)
				Nnz.append(len(distribution_parameters[n]))

			else:

				#Check that number of parameters conforms to standard
				assert len(distribution_parameters[n])==_nicaea_builtin[distr_in_bin],"You must provide exactly {0} parameters for distribution {1}".format(_nicaea_builtin[distr_in_bin],distr_in_bin)
				Nnz.append(len(distribution_parameters[n]))

		#Build the ordered array par_nz
		assert len(Nnz)==nzbins
		par_nz = np.concatenate(distribution_parameters)


	#Return in NICAEA friendly format
	return nzbins,nofz,Nnz,par_nz




##########################################
##########NicaeaSettings class############
##########################################

class NicaeaSettings(dict):

	"""
	Class handler of the code settings (non linear modeling, tomography, transfer function, etc...)
	"""

	def __init__(self):

		super(NicaeaSettings,self).__init__()
		
		#Default settings
		self["snonlinear"]="smith03"
		self["stransfer"]="eisenhu"
		self["sgrowth"]="growth_de"
		self["sde_param"]="linder"
		self["normmode"]="norm_s8"
		self["stomo"]="tomo_all"
		self["sreduced"]="none"
		self["q_mag_size"]=1.0

	@classmethod
	def default(cls):

		"""
		Generate default settings

		:returns: NicaeaSettings defaults instance

		"""

		return cls()

	@property
	def knobs(self):

		"""
		Lists available settings to tune

		"""

		return self.keys()

	def available(self,knob):

		"""
		Given a settings, lists all the possible values

		"""
		
		#Available settings
		if knob=="snonlinear":
			return [ "linear", "pd96", "smith03", "smith03_de", "coyote10", "coyote13", "halodm", "smith03_revised" ]
		elif knob=="stransfer":
			return [ "bbks", "eisenhu", "eisenhu_osc", "be84" ]
		elif knob=="sgrowth":
			return [ "heath", "growth_de" ]
		elif knob=="sde_param":
			return [ "jassal", "linder", "earlyDE", "poly_DE" ]
		elif knob=="normmode":
			return [ "norm_s8" , "norm_as" ]
		elif knob=="stomo":
			return [ "tomo_all", "tomo_auto_only", "tomo_cross_only" ]
		elif knob=="sreduced":
			return ["none", "reduced_K10"]
		elif knob=="q_mag_size":
			print("Positive float")
			return None
		else:
			raise ValueError("{0} is not a tunable setting!".format(knob)) 




##########################################
##########Nicaea class####################
##########################################

class Nicaea(w0waCDM):

	"""
	Main class handler for the python bindings of the NICAEA cosmological code, written by M. Kilbinger & collaborators

	"""

	def __init__(self,H0=72.0,Om0=0.26,Ode0=0.74,Ob0=0.046,w0=-1.0,wa=0.0,sigma8=0.798,ns=0.960,name=None):

		if _nicaea is None:
			raise ImportError("The Nicaea bindings were not installed, check your GSL/FFTW3 installations!")

		super(Nicaea,self).__init__(H0,Om0,Ode0,w0=w0,wa=wa,Ob0=Ob0,name=name)
		self.sigma8=sigma8
		self.ns=ns

	def __repr__(self):

		astropy_string = super(Nicaea,self).__repr__()
		pieces = astropy_string.split(",")
		si8_piece = u" sigma8={0}".format(self.sigma8)
		ns_piece = u" ns={0}".format(self.ns)
		Ob0_piece = u" Ob0={0}".format(self.Ob0)

		return ",".join(pieces[:3] + [si8_piece,ns_piece,Ob0_piece] + pieces[3:])

	@classmethod
	def fromCosmology(cls,cosmo):

		"""
		Builds a Nicaea instance from one of astropy.cosmology objects, from which it inherits all the cosmological parameter values

		:param cosmo: one of astropy cosmology instances
		:type cosmo: astropy FLRW

		:returns: Nicaea instance with the cosmological parameters inherited from cosmo 

		"""

		#Get the cosmological parameter values out of the cosmo object
		H0 = cosmo.H0.value
		Om0 = cosmo.Om0
		Ode0 = cosmo.Ode0

		#Dark energy
		if hasattr(cosmo,"w0"):
			w0=cosmo.w0
		else:
			w0=-1.0

		if hasattr(cosmo,"wa"):
			wa=cosmo.wa
		else:
			wa=0.0

		#Neutrinos
		Neff = cosmo.Neff
		Onu0 = cosmo.Onu0

		#Set these manually to default
		ns = 0.960
		sigma8 = 0.800
		Ob0 = 0.046

		#Instantiate
		return cls(H0=H0,Om0=Om0,Ode0=Ode0,Ob0=Ob0,w0=w0,wa=wa,sigma8=sigma8,ns=ns)


	def convergencePowerSpectrum(self,ell,z=2.0,distribution=None,distribution_parameters=None,settings=None,**kwargs):

		"""
		Computes the convergence power spectrum for the given cosmological parameters and redshift distribution using NICAEA

		:param ell: multipole moments at which to compute the power spectrum
		:type ell: array.

		:param z: redshift bins for the sources; if a single float is passed, single redshift is assumed
		:type z: float., array or None

		:param distribution: redshift distribution of the sources (normalization not necessary); if None a single redshift is expected; if callable, z must be an array, and a single redshift bin is considered, with the galaxy distribution specified by the call of distribution(z); if a list is passed, each element must be a NICAEA type
		:type distribution: None,callable or list

		:param distribution_parameters: relevant only when distribution is a list or callable. When distribution is callable, distribution_parameters has to be one between "one" and "all" to decide if one or multiple redshift bins have to be considered. If it is a list, each element in it should be the tuple of parameters expected by the correspondent NICAEA distribution type
		:type distribution_parameters: str. or list.

		:param settings: NICAEA code settings
		:type settings: NicaeaSettings instance

		:param kwargs: the keyword arguments are passed to the distribution, if callable
		:type kwargs: dict.

		:returns: ( NlxNz array ) computed power spectrum at the selected multipoles (when computing the cross components these are returned in row major C ordering)

		"""

		assert isinstance(ell,np.ndarray)

		#If no settings provided, use the default ones
		if settings is None:
			settings=NicaeaSettings.default()

		#Check sanity of input
		nzbins,nofz,Nnz,par_nz = _check_redshift(z,distribution,distribution_parameters,**kwargs)

		#Compute the power spectrum via NICAEA
		power_spectrum_nicaea = _nicaea.shearPowerSpectrum(self.Om0,self.Ode0,self.w0,self.wa,self.H0.value/100.0,self.Ob0,self.Onu0,self.Neff,self.sigma8,self.ns,nzbins,ell,Nnz,nofz,par_nz,settings,None)
		
		#Return
		if power_spectrum_nicaea.shape[1]==1:
			return power_spectrum_nicaea[:,0]
		else:
			return power_spectrum_nicaea


	def shearTwoPoint(self,theta,z=2.0,distribution=None,distribution_parameters=None,settings=None,kind="+",**kwargs):

		"""
		Computes the shear two point function for the given cosmological parameters and redshift distribution using NICAEA

		:param theta: angles at which to compute the two point function 
		:type theta: array. with units

		:param z: redshift bins for the sources; if a single float is passed, single redshift is assumed
		:type z: float., array or None

		:param distribution: redshift distribution of the sources (normalization not necessary); if None a single redshift is expected; if callable, z must be an array, and a single redshift bin is considered, with the galaxy distribution specified by the call of distribution(z); if a list is passed, each element must be a NICAEA type
		:type distribution: None,callable or list

		:param distribution_parameters: relevant only when distribution is a list or callable. When distribution is callable, distribution_parameters has to be one between "one" and "all" to decide if one or multiple redshift bins have to be considered. If it is a list, each element in it should be the tuple of parameters expected by the correspondent NICAEA distribution type
		:type distribution_parameters: str. or list.

		:param settings: NICAEA code settings
		:type settings: NicaeaSettings instance

		:param kind: must be "+" or "-"
		:type kind: str.

		:param kwargs: the keyword arguments are passed to the distribution, if callable
		:type kwargs: dict.

		:returns: ( NtxNz array ) computed two point function at the selected angles (when computing the cross components these are returned in row major C ordering)

		"""

		assert isinstance(theta,np.ndarray)

		#If no settings provided, use the default ones
		if settings is None:
			settings=NicaeaSettings.default()

		#Convert angles in radians
		theta_rad = theta.to(rad).value

		#Check sanity of input
		nzbins,nofz,Nnz,par_nz = _check_redshift(z,distribution,distribution_parameters,**kwargs)

		#Plus or minus?
		if kind=="+":
			pm = 1
		elif kind=="-":
			pm = -1
		else:
			raise ValueError("kind must be either + or -")

		#Compute the two point function using NICAEA
		two_point_function_nicaea = _nicaea.shear2pt(self.Om0,self.Ode0,self.w0,self.wa,self.H0.value/100.0,self.Ob0,self.Onu0,self.Neff,self.sigma8,self.ns,nzbins,theta_rad,Nnz,nofz,par_nz,settings,pm)

		#Return
		if two_point_function_nicaea.shape[1]==1:
			return two_point_function_nicaea[:,0]
		else:
			return two_point_function_nicaea



