def construir_cliLine(m, datos, lenData, mop=None):

    system  = datos.ip
    rtrName = datos.name
    intName = datos.intName
    port    = datos.port
    ipAddr  = datos.intAddr

    title    = ""
    cfg      = "" 

	# We want a title for each router with Heading 2...
    if mop and m == 0:
        cfg = "\nHeading_2:Router: " + rtrName + " (" + system + ")\n"

    # Configure interfaces ...
    if intName == "loop0":
		
        # We want a subtitle with Heading 3...
        if mop:
            cfg = cfg + "\nHeading_3:Loopback Interface\n"
        
        cfg = cfg + "/configure router interface " + intName + " loopback " + "\n"
        cfg = cfg + "/configure router interface " + intName + " address " + ipAddr + "\n"

    else:

        # We want a subtitle with Heading 3...
        # We have more than one WanInt, so the title is needed only once, the first time (m==0).
        if mop and m == 0:
            cfg = cfg + "\nHeading_3:Wan Interface\n"
                
        cfg = cfg + "/configure router interface " + intName + " port " + port + "\n"
        cfg = cfg + "/configure router interface " + intName + " address " + ipAddr + "\n"

    return cfg
