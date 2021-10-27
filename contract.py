import smartpy as sp

class Escrow(sp.Contract):
    def __init__(self, owner, fromOwner, counterparty, fromCounterparty, epoch, hashedSecret):
        self.init(fromOwner           = fromOwner,
                  fromCounterparty    = fromCounterparty,
                  balanceOwner        = sp.tez(0),
                  balanceCounterparty = sp.tez(0),
                  hashedSecret        = hashedSecret,
                  epoch               = epoch,
                  owner               = owner,
                  counterparty        = counterparty)

    @sp.entry_point
    def addBalanceOwner(self):
        sp.verify(self.data.owner == sp.sender , "Wrong Owner")
        sp.verify(self.data.balanceOwner == sp.tez(0) , "There is already some stake")
        sp.verify(sp.amount == self.data.fromOwner , "Only the stake amount is allowed")
        self.data.balanceOwner = self.data.fromOwner

    @sp.entry_point
    def addBalanceCounterparty(self):
        sp.verify(self.data.counterparty == sp.sender , "Wrong CounterParty")
        sp.verify(self.data.balanceCounterparty == sp.tez(0) , "There is already some stake")
        sp.verify(sp.amount == self.data.fromCounterparty , "Only the stake amount is allowed")
        self.data.balanceCounterparty = self.data.fromCounterparty

    def claim(self, identity):
        sp.verify(sp.sender == identity , "Wrong Identity. Internal call only")
        sp.send(identity, self.data.balanceOwner + self.data.balanceCounterparty)
        self.data.balanceOwner = sp.tez(0)
        self.data.balanceCounterparty = sp.tez(0)

    @sp.entry_point
    def claimCounterparty(self, params):
        sp.verify(sp.now < self.data.epoch , "Time limit expired")
        sp.verify(self.data.hashedSecret == sp.blake2b(params.secret) , "Wrong Secret Key")
        self.claim(self.data.counterparty)

    @sp.entry_point
    def claimOwner(self):
        sp.verify(self.data.epoch < sp.now , "Time Limit not yet reached")
        self.claim(self.data.owner)

@sp.add_test(name = "Escrow")
def test():
    #Test Scenario
    scenario = sp.test_scenario()
    scenario.h1("Escrow")

    #Test Accounts
    bob = sp.test_account("Bob")
    udit = sp.test_account("Udit")

    #Origination
    s = sp.pack("SECRETKEY") #String to Bytes
    secret = sp.blake2b(s) #Hashing bytes to secret key
    ob = Escrow(bob.address, sp.tez(25), udit.address, sp.tez(5), sp.timestamp(1634753427), secret)
    scenario += ob

    scenario.h1("Workflows")
    scenario.h2("Add Balance Owner")
    #addBalanceOwner Tests
    ob.addBalanceOwner().run(sender=udit , amount = sp.tez(25) , valid = False)
    ob.addBalanceOwner().run(sender=bob , amount = sp.tez(1) , valid = False)

    ob.addBalanceOwner().run(sender = bob, amount = sp.tez(25))

    ob.addBalanceOwner().run(sender = bob , amount = sp.tez(25) , valid = False)


    scenario.h2("Add Balance CounterParty")
    #addBalanceCounterparty Tests
    ob.addBalanceCounterparty().run(sender=bob , amount = sp.tez(5) , valid = False)
    ob.addBalanceCounterparty().run(sender=udit , amount = sp.tez(25) , valid = False)

    ob.addBalanceCounterparty().run(sender = udit, amount = sp.tez(5))

    ob.addBalanceCounterparty().run(sender = udit, amount = sp.tez(5) , valid = False)

    scenario.h2("Claim CounterParty")
    #claimCounterparty Tests
    ob.claimCounterparty(secret = s).run(sender = bob , valid = False)
    ob.claimCounterparty(secret = sp.bytes("0x01223343")).run(sender = udit, valid = False)
    ob.claimCounterparty(secret = s).run(sender = udit , now = sp.timestamp(1635192186) , valid=False)

 
    # ob.claimCounterparty(secret = s).run(sender = udit)

    scenario.h2("Claim Owner")
    #claimOwner Tests
    ob.claimOwner().run(sender = udit , valid = False)
    ob.claimOwner().run(sender = bob, valid=False)

 
    ob.claimOwner().run(sender = bob ,now = sp.timestamp(1635192186) )

    scenario.verify(ob.data.owner == bob.address)
    x = scenario.compute(ob.data.fromOwner + sp.tez(15))
    scenario.show(ob.data)
    scenario.show(ob.data.fromOwner + sp.tez(15))
