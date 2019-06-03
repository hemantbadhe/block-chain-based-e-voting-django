import time, datetime
import uuid
from Crypto.Signature import DSS
from Crypto.Hash import SHA3_256
from Crypto.PublicKey import ECC
from Crypto import Random
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from simulation.merkle.merkle_tool import MerkleTools
from simulation.models import *


@login_required(login_url='/')
def create(request):
    if request.method == 'POST':
        voter_id = request.POST.get('voter-id-input')
        vote = request.POST.get('vote-input')
        private_key = request.POST.get('private-key-input')

        # Create ballot as string vector
        timestamp = datetime.datetime.now().timestamp()
        ballot = "{}|{}|{}".format(voter_id, vote, timestamp)
        print('\ncasted ballot: {}\n'.format(ballot))

        # get user object for public key
        user_obj = User.objects.get(id=request.user.id)
        signature = ''
        try:
            # Create signature
            priv_key = ECC.import_key(private_key)
            h = SHA3_256.new(ballot.encode('utf-8'))
            signature = DSS.new(priv_key, 'fips-186-3').sign(h)
            print('\nsignature: {}\n'.format(signature.hex()))

            # Verify the signature using registered public key
            pub_key = ECC.import_key(user_obj.public_key)
            # pub_key = ECC.import_key(settings.PUBLIC_KEY)
            verifier = DSS.new(pub_key, 'fips-186-3')

            verifier.verify(h, signature)

            #  create vote object
            block_no = Vote.objects.count()
            block_no += 1
            vote_obj = Vote.objects.create(id=voter_id, vote=vote, block_id=block_no)
            vote_backup_obj = VoteBackup.objects.create(id=voter_id, vote=vote, block_id=block_no)
            vote_obj.save()
            vote_backup_obj.save()

            status = 'The ballot is signed successfully.'
            error = False
            vote_obj = vote_obj
        except (ValueError, TypeError):
            status = 'The key is not registered.'
            error = True
            vote_obj = None

        context = {
            'ballot': ballot,
            'signature': signature,
            'status': status,
            'error': error,
            'vote_obj': vote_obj
        }
        return render(request, 'ballot/status.html', context)

    context = {'voter_id': uuid.uuid4(), }
    return render(request, 'ballot/create.html', context)


@login_required(login_url='/')
def seal(request):
    if request.method == 'POST':
        ballot = request.POST.get('ballot_input')
        vote_obj_id = request.POST.get('vote_obj_id')
        # ballot_byte = ballot.encode('utf-8')
        # ballot_hash = SHA3_256.new(ballot_byte).hexdigest()
        # # Puzzle requirement: '0' * n (n leading zeros)
        # puzzle, pcount = settings.PUZZLE, settings.PLENGTH
        # nonce = 0
        #
        # # Try to solve puzzle
        # start_time = time.time()  # benchmark
        # timestamp = datetime.datetime.now().timestamp()  # mark the start of mining effort
        # while True:
        #     block_hash = SHA3_256.new(("{}{}{}".format(ballot, nonce, timestamp).encode('utf-8'))).hexdigest()
        #     print('\ntrial hash: {}\n'.format(block_hash))
        #     print(nonce)
        #     if block_hash[:pcount] == puzzle:
        #         stop_time = time.time()  # benchmark
        #         print("\nblock is sealed in {} seconds\n".format(stop_time - start_time))
        #         break
        #     nonce += 1
        #
        # context = {
        #     'prev_hash': 'GENESIS',
        #     'transaction_hash': ballot_hash,
        #     'nonce': nonce,
        #     'block_hash': block_hash,
        #     'timestamp': timestamp,
        # }

        puzzle, pcount = settings.PUZZLE, settings.PLENGTH

        # Seal transactions into blocks
        time_start = time.time()
        number_of_blocks = 1

        block_count = Block.objects.all().last()
        if not block_count:
            prev_hash = '0' * 64
        else:
            prev_hash = block_count.h

        vote_obj = Vote.objects.filter(id=vote_obj_id)
        # for i in range(1, number_of_blocks + 1):
        block_transactions = vote_obj
        root = MerkleTools()
        root.add_leaf([str(tx) for tx in vote_obj], True)
        root.make_tree()
        merkle_h = root.get_merkle_root()

        # Try to seal the block and generate valid hash
        nonce = 0
        timestamp = datetime.datetime.now().timestamp()
        while True:
            enc = ("{}{}{}{}".format(prev_hash, merkle_h, nonce, timestamp)).encode('utf-8')
            h = SHA3_256.new(enc).hexdigest()
            if h[:pcount] == puzzle:
                break
            nonce += 1

        # Create the block
        block = Block(prev_h=prev_hash, merkle_h=merkle_h, h=h, nonce=nonce, timestamp=timestamp)
        block.save()
        print('\nBlock {} is mined\n')
        # Set this hash as prev hash
        prev_hash = h

        time_end = time.time()
        print('\nSuccessfully created {} blocks.\n'.format(number_of_blocks))
        print('\nFinished in {} seconds.\n'.format(time_end - time_start))
        # return render(request, 'ballot/seal.html')
        return redirect('/sim/transactions/')
    return redirect('ballot:create')
