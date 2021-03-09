def construir_cliLine(m, datos, mop=None):

	ipSystem   = datos[0]
	router     = datos[1]
	port       = datos[2]
	intName    = datos[3]
	address    = datos[4]

	cfg        = ""
	title      = ""

	if mop:
		title = "\nRouter: " + router + ", " + ipSystem + "\n"

	cfg = cfg + "/configure router interface " + intName + " port " + port + "\n"
	cfg = cfg + "/configure router interface " + intName + " address " + address + "\n"

	if mop:
		return title + cfg
	else:
		return cfg