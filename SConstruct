import distutils.sysconfig

import numpy
import os
from defaults import *
import atexit

Export('codePath')

gcv = distutils.sysconfig.get_config_var

AddOption('--prefix',
        dest='prefix',
        type='string',
        nargs=1,
        action='store',
        metavar='DIR',
        default=defaultPrefix,
        help='installation prefix - defaults to ' + defaultPrefix)

AddOption('--with-url',
        dest='url',
        type='string',
        nargs=1,
        action='store',
        default=defaultURL,
        help='Set url for the website.  Default ' + defaultURL)

AddOption('--with-apbs',
        dest='apbs',
        type='string',
        nargs=1,
        action='store',
        default="",
        help='Location of APBS install.')

AddOption('--with-default-opal',
        dest='opal',
        action='store_const',
        const=defaultOpalURL,
        help='Use default URL for Opal service -> '+defaultOpalURL)

AddOption('--with-opal',
        dest='opal',
        type='string',
        nargs=1,
        action='store',
        default='',
        help='Set URL for Opal service')

AddOption('--with-default-apbs-opal',
        dest='apbs_opal',
        action='store_const',
        const=defaultAPBSOpalURL,
        help='Set URL for APBS Opal service -> '+defaultAPBSOpalURL)

AddOption('--with-apbs-opal',
        dest='apbs_opal',
        type='string',
        nargs=1,
        action='store',
        default='',
        help='Set URL for APBS Opal service.')

AddOption('--with-max-atoms',
        dest='max_atoms',
        type='int',
        nargs=1,
        action='store',
        default=defaultMaxAtoms,
        help='Sets the maximum number of atoms in '+\
             'a protein for non-Opal job submission. '+\
             'Only affects web tools. Default is '+\
             str(defaultMaxAtoms))

AddOption('--disable-pdb2pka',
        dest='pdb2pka',
        action='store_false',
        default=True,
        help='Disable pkb2pka compilation. pdb2pka is required for ligand support.')

AddOption('--rebuild-swig-bindings',
        dest='swig',
        action='store_true',
        default=False,
        help='Rebuild swig bindings for pdb2pka. Requires swig be installed. In Windows swig must be in your PATH.')

AddOption('--rebuild-docs',
        dest='docs',
        action='store_true',
        default=False,
        help='Rebuild pydocs.')

AddOption('--long-test-count',
        dest='longTestCount',
        action='store',
        type=int,
        help='When building the long-test target specify how many tests to run.')


if os.name == 'nt':
    tool_chain = ['mingw']
else:
    tool_chain = ['default']
    
env = Environment(tools=tool_chain + ['swig'], 
                  SWIGFLAGS=['-python', '-c++'], 
                  SHLIBPREFIX="", 
                  SHLIBSUFFIX=gcv('SO'))

env.Append(CPPPATH=[distutils.sysconfig.get_python_inc(), numpy.get_include()])

if os.name == 'nt':
    python_root = sys.prefix
    python_version = '%u%u' % sys.version_info[:2]
    python_include = os.path.join(python_root, 'include')
    python_libs = os.path.join(python_root, 'libs')
    python_lib = 'python' + python_version
    env.Append(LIBPATH=[python_libs])
    env.Append(LIBS=[python_lib])
    env.Append(ENV={'PATH' : os.environ['PATH']})
    
Export('env')

prefix = GetOption('prefix')
prefix = prefix.replace('\\', '/')
if prefix[-1] != '/':
    prefix+='/'
    
url = GetOption('url')
#Not sure if this is needed.
if url is not None:
    submitAction = url+'/pdb2pqr.cgi'
else:
    url = defaultURL
    #Can it always just be this?  
    submitAction = 'pdb2pqr.cgi'

maxatomsStr = str(GetOption('max_atoms'))
               
replacementDict = {'@WHICHPYTHON@':pythonBin,
                   '@INSTALLDIR@':prefix,
                   '@MAXATOMS@':maxatomsStr,
                   '@website@':url,
                   '@srcpath@':codePath,
                   '@PDB2PQR_VERSION@':productVersion,
                   '@action@':submitAction,
                   '@APBS_LOCATION@':GetOption('apbs'),
                   '@APBS_OPAL_URL@':GetOption('apbs_opal'),
                   '@PDB2PQR_OPAL_URL@':GetOption('opal')}

#If any replacement strings change recompile those files.
#As the product version can be based on the time this may
# rebuild string replacement files after less than one minute between builds
settingsValues = env.Value(replacementDict)

#We have a separate dict for server.html.in as we need to use regex
#Regex does not play nice with some  possible user strings
#Set up regex to alternately clear tags or wipe sections
if GetOption('opal') == '':
    #Not using opal for pdb2pqr.
    withOpalRegex = '@WITHOPAL@'
    withoutOpalRegex = r'@WITHOUTOPAL@.*?@WITHOUTOPAL@'
else:
    #Using opal for pdb2pqr.
    withOpalRegex = r'@WITHOPAL@.*?@WITHOPAL@'
    withoutOpalRegex = '@WITHOUTOPAL@'

    
serverHtmlDict = {'@website@':url,
                  '@PDB2PQR_VERSION@':productVersion,
                  '@MAXATOMS@':maxatomsStr,
                  '@action@':submitAction,
                  withOpalRegex:'',
                  withoutOpalRegex:''}

chmodAction = Chmod('$TARGET', 0755)
serverHtmlCopySub = CopySub('$TARGET', '$SOURCE', serverHtmlDict, useRegex=True)
normalCopySub = CopySub('$TARGET', '$SOURCE', replacementDict, useRegex=False)

subFiles = [('pdb2pqr.py', 'pdb2pqr.py.in', True),
            ('apbs_cgi.cgi', 'apbs_cgi.py', True),
            ('visualize.cgi', 'visualize.py', True),
            ('querystatus.cgi', 'querystatus.py', True),
            ('src/aconf.py', 'src/aconf.py.in', False),
            ('html/server.html', 'html/server.html.in', False)]

for target, source, chmod in subFiles:        
    actions = [normalCopySub] if target != 'html/server.html' else [serverHtmlCopySub]
    if chmod:
        actions.append(chmodAction)
    result = env.Command(target, source, actions)
    if target == 'pdb2pqr.py':
        pdb2pqr = result
        Export('pdb2pqr')        
    Default(result)
    Depends(result, settingsValues)

Default(env.Command('pdb2pqr.cgi', 'pdb2pqr.py', Copy('$TARGET', '$SOURCE')))



if GetOption('pdb2pka'):
    SConscript('pdb2pka/SConscript')
    
SConscript('tests/SConscript')

def print_default_message(target_list):
    target_list = map(str, target_list)
    if any('test' in x for x in target_list):
        return
    if GetOption("clean"):
        return
    print
    print 'TARGETS:', target_list
    print
    print '========================'
    print 'Configuration Parameters'
    print '========================'
    print
    print 'Version:', productVersion
    print 'Install directory:', prefix
    print 'pdb2pka and ligand support:', GetOption('pdb2pka')
    print 'Path to the website directory:', url
    if GetOption('opal') == '':
        print 'PDB2PQR jobs run via the web interface will be forked on the server'
    else:
        print 'PDB2PQR jobs run via the web interface will be run via opal at', GetOption('opal') 
    print
    print 'Run "./scons.py install" to install pdb2pqr in', prefix
    print 'Run "./scons.py test", "./scons.py advtest", or "./scons.py completetest" to run various pdb2pqr tests.'
    print 'To setup a web service create a symbolic link to', prefix, 'that enables you to view', url,'after running "./scons.py install"'
    
atexit.register(print_default_message, BUILD_TARGETS)
