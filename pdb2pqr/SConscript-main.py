import distutils.sysconfig

import os
from defaults import *
import atexit

Export('codePath')

config_file = 'build_config.py'

gcv = distutils.sysconfig.get_config_var

vars = Variables(['.variables.cache', config_file], ARGUMENTS)

vars.Add(PathVariable('PREFIX',
                      'Install directory',
                      defaultPrefix,
                      PathVariable.PathAccept))
                      
vars.Add('URL', "Sets the url of pdb2pqr's web interface.", defaultURL)

vars.Add('OPAL', 'Sets the url of a pdb2pqr opal service.', '')
vars.Add('APBS_OPAL', 'Sets the url of a apbs opal service.', '')

vars.Add(PathVariable('APBS',
                      'Location of the APBS binary if installed',
                      '',
                      PathVariable.PathAccept))
                      
vars.Add('MAX_ATOMS', 'Sets the maximum number of atoms in a protein for non-Opal job submission. '
					  'Only affects web tools', 10000, None, int)
					  
vars.Add(BoolVariable('BUILD_PDB2PKA', 
					  'Set to False to skip building ligand and pdb2pka support. Requires numpy.',
					  True))
					  
vars.Add(BoolVariable('REBUILD_SWIG', 
					  'Set to True to rebuild the swig bindings. Requires swig on the the user path.',
					  False))

vars.Add(BoolVariable('DEBUG', 
                      'Set to True to compiled components with debug headers.',
                      False))

#TODO: setup rebuilding of docs.
# THIS SHOULD BE A TARGET!
#AddOption('--rebuild-docs',
#        dest='docs',
#        action='store_true',
#        default=False,
#        help='Rebuild pydocs.')

#Windows: make sure we use correct target arch. 
target_arch='x86_64'
import platform
arch = platform.architecture()
bit_str = arch[0]
if bit_str == '32bit':
    target_arch='x86'

if os.name == 'nt':
    #tool_chain = ['mingw']
    tool_chain = ['default', 'mssdk']
else:
    tool_chain = ['default']
    
tool_chain.append('swig')
    
env = Environment(variables=vars,
                  MSVC_VERSION='9.0',
                  TARGET_ARCH=target_arch,
                  MSSDK_VERSION='6.0A',
                  tools=tool_chain, 
                  SWIGFLAGS=['-python', '-c++'], 
                  SHLIBPREFIX="", 
                  SHLIBSUFFIX=gcv('SO'),
                  LDMODULESUFFIX=gcv('SO'))



python_lib = 'python' + gcv('VERSION')
env.Append(LIBS=[python_lib])
#To get swig to work on windows.
#env.Append(ENV={'PATH' : os.environ['PATH']})

if os.name == 'nt' and 'mingw' not in tool_chain:
    env.Append(CXXFLAGS = ['/EHsc'])

if env['DEBUG']:
    if os.name == 'nt' and 'mingw' not in tool_chain:
        env.Append(CXXFLAGS = ['/DEBUG'])
    else:
        env.MergeFlags('-g')

if os.name == 'nt':
    python_root = sys.prefix    
    python_include = os.path.join(python_root, 'include')
    python_libs = os.path.join(python_root, 'libs')    
    env.Append(LIBPATH=[python_libs])
else:
    env.Append(LIBPATH=[gcv('LIBDIR')])
    
Export('env')

prefix = env['PREFIX']
prefix = prefix.replace('\\', '/')
if not prefix.endswith('/'):
    prefix+='/'
    
env['PREFIX'] = prefix

Help(vars.GenerateHelpText(env))

vars.Save('.variables.cache', env)

#Not the optimal way to do this...
#Should figure out how to do it with a delete command
Clean('pdb2pqr.py', '.variables.cache')
  
url = env['URL']
#Not sure if this is needed.
if url is not None:
    if not url.endswith('/'):
        url += '/'
    submitAction = url+'pdb2pqr.cgi'
else:
    url = defaultURL
    #Can it always just be this?  
    submitAction = 'pdb2pqr.cgi'

maxatomsStr = str(env['MAX_ATOMS'])
               
replacementDict = {'@WHICHPYTHON@':pythonBin,
                   '@INSTALLDIR@':prefix,
                   '@MAXATOMS@':maxatomsStr,
                   '@website@':url,
                   '@srcpath@':codePath,
                   '@PDB2PQR_VERSION@':productVersion,
                   '@action@':submitAction,
                   '@APBS_LOCATION@':env['APBS'],
                   '@APBS_OPAL_URL@':env['APBS_OPAL'],
                   '@PDB2PQR_OPAL_URL@':env['OPAL']}

#If any replacement strings change recompile those files.
#As the product version can be based on the time this may
# rebuild string replacement files after less than one minute between builds
settingsValues = env.Value(replacementDict)

#We have a separate dict for server.html.in as we need to use regex
#Regex does not play nice with some  possible user strings
#Set up regex to alternately clear tags or wipe sections
if env['OPAL'] == '':
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

compile_targets = []

for target, source, chmod in subFiles:        
    actions = [normalCopySub] if target != 'html/server.html' else [serverHtmlCopySub]
    if chmod:
        actions.append(chmodAction)
    result = env.Command(target, source, actions)
    compile_targets.append(result)
    if target == 'pdb2pqr.py':
        pdb2pqr = result
        Export('pdb2pqr')        
    Default(result)
    Depends(result, settingsValues)

Default(env.Command('pdb2pqr.cgi', 'pdb2pqr.py', Copy('$TARGET', '$SOURCE')))

#Check to see why we can't build pdb2pka.
numpy_error = False
if env['BUILD_PDB2PKA']:
    try:
        import numpy
    except ImportError:
        print 'WARNING: PDB2PKA build skipped, numpy not installed. Ligand support will not be available.'
        numpy_error = True
    
    if not numpy_error:
        compile_targets.extend(SConscript('pdb2pka/SConscript'))
    
SConscript('tests/SConscript')

SConscript('SConscript-install.py', exports='env compile_targets')

SConscript('SConscript-error.py')

with open('env64.txt', 'w') as f:
    f.write(env.Dump())

def print_default_message(target_list):
    target_list = map(str, target_list)
    if any('test' in x for x in target_list):
        return
    if GetOption("clean"):
        return
    if not GetOption("help"):
        
        print
        print 'TARGETS:', target_list
        print
        print '========================'
        print 'Configuration Parameters'
        print '========================'
        print
        print 'Version:', productVersion
        print 'Install directory:', env['PREFIX']
        if numpy_error:
            print
            print 'WARNING: PDB2PKA build skipped, numpy not installed. Ligand support will not be available.'
            print
        else: 
            print 'pdb2pka and ligand support:', env['BUILD_PDB2PKA']
        print 'Path to the website directory:', url
        if env['OPAL'] == '':
            print 'PDB2PQR jobs run via the web interface will be forked on the server.'
        else:
            print 'PDB2PQR jobs run via the web interface will be run via opal at', env['OPAL']
    else:
        print
        print 'Run "python scons/scons.py" to build pdb2pqr.'
        
    print
    print 'The preferred way to configure the build is by editing the file', config_file        
    print
    print 'Run scons with the python that you intend to use with pdb2pqr.'
    print 'For example: "/opt/bin/python scons/scons.py" will setup pdb2pqr to be run with /opt/bin/python'
    
    if 'install' not in target_list:
        print
        print 'Run "python scons/scons.py install" to install pdb2pqr in', env['PREFIX']
    
    print    
    print 'Run "python scons/scons.py basic-test" for a basic functionality test'
    print 'Run "python scons/scons.py advanced-test" for a single test of ligand and PROPKA support. Requires numpy and PDB2PKA support compiled.'
    print 'Run "python scons/scons.py complete-test" for a complete test of all functionality EXCEPT PDB2PKA. Requires numpy and PDB2PKA support compiled.'
    print 'Run "python scons/scons.py pdb2pka-test" for a simple test of PDB2PKA functionality.'
    print '    Requires numpy, PDB2PKA support compiled AND the APBS python libraries compiled and installed in the pdb2pka directory.'
    
    print 
    print 'To setup a web service create a symbolic link to', env['PREFIX'], 'that enables you to view', env['URL'],'after running "scons/scons.py install"'

    
    if 'install' in target_list:
        print
        print 'pdb2pqr installed in', env['PREFIX']
    
    
atexit.register(print_default_message, BUILD_TARGETS)
