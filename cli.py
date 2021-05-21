import sys
import requests

if(len(sys.argv)==1):
    print("Please run the CLI providing as parameter the port of the client. Thank you.")
    sys.exit(0)

port = sys.argv[1]
print()
print("Hello user! Choose an action:")
print("     1. t <recipient_id> <amount>")
print("     2. view")
print("     3. balance")
print("     4. help")
print("     5. exit")


base_url = "http://127.0.0.1:" + port + "/"

NODES = 5

continue_run = True
while(continue_run):
    print()
    action = input() 
    if(action[0]=='t'):
        inputs = action.split()
        receiver_id = inputs[1]
        amount = inputs[2]
        if (int(receiver_id) > NODES-1):
            print("ids must be from 0 to " + str(NODES-1))
        else:
            url = base_url+"transaction/create/" + str(receiver_id) + "/" + str(amount)
            inputs = action.split()
            response = requests.get(url)

    elif(action=='balance'):
        url = base_url+"nodes/showbalance"
        response = requests.get(url)
        print(response.json())

    elif(action=='view'):
        url = base_url+"transactions/get"
        response = requests.get(url)
        print(response.json())
        
    elif(action == 'help'):
        print()
        print("Here are the available actions")
        print()
        print("     1. Type 't <recipient_id> <amount>', in order to create a new transaction\n        and send <amount> NBC to client with node id = <recipient_address>.")
        print()
        print("     2. Type 'view', in order to view all transactions of the last validated block.")
        print()
        print("     3. Type 'balance', in order to view your wallet balance.")
        print()
        print("     4. Type 'help' for more information.")
        print()
        print("     5. Type 'exit', in order to exit .")

    elif(action=='exit'):
        continue_run = False
        print("Closing...")
        sys.exit(0)
        
    else:
        print("Invalid action. Please select a valid action, or type 'help' for more information.")
